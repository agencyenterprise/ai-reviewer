"""Unit tests for the view_image tool."""

import base64
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from langchain_core.messages import AIMessage, ToolMessage

from lib.agents.tools.view_image import (
    MAX_IMAGE_BYTES,
    _parse_image_file_id,
    redact_image_blocks,
    view_image,
    view_image_for_conversation,
)
from lib.models.file import FileRole

PROJECT_ID = uuid.uuid4()
IMAGE_ID = uuid.uuid4()
PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-image-bytes"


def _runtime(project_id: uuid.UUID = PROJECT_ID) -> MagicMock:
    runtime = MagicMock()
    runtime.context.project_id = str(project_id)
    return runtime


def _image_file(tmp_path, **overrides) -> MagicMock:
    path = tmp_path / "image.png"
    path.write_bytes(PNG_BYTES)
    file = MagicMock()
    file.id = IMAGE_ID
    file.project_id = PROJECT_ID
    file.conversation_id = None
    file.role = FileRole.EXTRACTED_IMAGE
    file.file_type = "image/png"
    file.file_size = len(PNG_BYTES)
    file.file_path = str(path)
    for key, value in overrides.items():
        setattr(file, key, value)
    return file


def _patched_lookup(file=None, side_effect=None):
    return patch(
        "lib.agents.tools.view_image.get_file_by_id",
        new=AsyncMock(return_value=file, side_effect=side_effect),
    )


class TestParseImageFileId:
    def test_full_reference_with_size_params(self):
        ref = f"draftdetective://{IMAGE_ID}?w=400&h=300"
        assert _parse_image_file_id(ref) == IMAGE_ID

    def test_reference_without_params(self):
        assert _parse_image_file_id(f"draftdetective://{IMAGE_ID}") == IMAGE_ID

    def test_bare_id(self):
        assert _parse_image_file_id(str(IMAGE_ID)) == IMAGE_ID

    def test_surrounding_whitespace_is_tolerated(self):
        assert _parse_image_file_id(f"  draftdetective://{IMAGE_ID} ") == IMAGE_ID

    @pytest.mark.parametrize(
        "reference",
        ["", "not-a-uuid", "draftdetective://not-a-uuid", "https://evil.example/x"],
    )
    def test_non_references_return_none(self, reference):
        assert _parse_image_file_id(reference) is None


class TestViewImage:
    @pytest.mark.asyncio
    async def test_returns_image_content_block(self, tmp_path):
        file = _image_file(tmp_path)
        with _patched_lookup(file):
            result = await view_image.coroutine(
                f"draftdetective://{IMAGE_ID}?w=400&h=300", _runtime()
            )

        assert isinstance(result, list)
        (block,) = result
        assert block["type"] == "image"
        assert block["source_type"] == "base64"
        assert block["mime_type"] == "image/png"
        assert base64.b64decode(block["data"]) == PNG_BYTES

    @pytest.mark.asyncio
    async def test_malformed_reference_is_rejected_without_lookup(self):
        with _patched_lookup(side_effect=AssertionError("must not be called")):
            result = await view_image.coroutine("figure-1", _runtime())

        assert isinstance(result, str)
        assert "not an image reference" in result

    @pytest.mark.asyncio
    async def test_unknown_id_reports_not_found_quietly(self, caplog):
        """A guessed or stale id is the expected miss, not an incident."""
        with _patched_lookup(side_effect=HTTPException(status_code=404)):
            result = await view_image.coroutine(str(IMAGE_ID), _runtime())

        assert isinstance(result, str)
        assert "no document image" in result
        assert not caplog.records

    @pytest.mark.asyncio
    async def test_lookup_outage_is_logged_but_reads_as_not_found(self, caplog):
        """The model must not be able to tell an outage from a missing file,
        but operators must."""
        with _patched_lookup(side_effect=RuntimeError("db down")):
            result = await view_image.coroutine(str(IMAGE_ID), _runtime())

        assert isinstance(result, str)
        assert "no document image" in result
        assert any("Could not look up" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_image_of_another_project_reports_not_found(self, tmp_path):
        """Ids come from model output: other projects' images must be invisible."""
        file = _image_file(tmp_path)
        with _patched_lookup(file):
            result = await view_image.coroutine(
                str(IMAGE_ID), _runtime(project_id=uuid.uuid4())
            )

        assert isinstance(result, str)
        assert "no document image" in result

    @pytest.mark.asyncio
    async def test_non_extracted_image_role_reports_not_found(self, tmp_path):
        """A MAIN file's id must not let the tool serve arbitrary project files."""
        file = _image_file(tmp_path, role=FileRole.MAIN)
        with _patched_lookup(file):
            result = await view_image.coroutine(str(IMAGE_ID), _runtime())

        assert isinstance(result, str)
        assert "no document image" in result

    @pytest.mark.asyncio
    async def test_unviewable_format_explains_instead_of_failing(self, tmp_path):
        file = _image_file(tmp_path, file_type="image/x-emf")
        with _patched_lookup(file):
            result = await view_image.coroutine(str(IMAGE_ID), _runtime())

        assert isinstance(result, str)
        assert "cannot be displayed" in result
        assert "image/x-emf" in result

    @pytest.mark.asyncio
    async def test_oversized_image_is_refused(self, tmp_path):
        file = _image_file(tmp_path, file_size=MAX_IMAGE_BYTES + 1)
        with _patched_lookup(file):
            result = await view_image.coroutine(str(IMAGE_ID), _runtime())

        assert isinstance(result, str)
        assert "too large" in result

    @pytest.mark.asyncio
    async def test_oversized_file_on_disk_is_refused_despite_small_metadata(
        self, tmp_path
    ):
        """The row's file_size is a hint; the cap must hold on the bytes read."""
        file = _image_file(tmp_path, file_size=1)
        with (
            _patched_lookup(file),
            patch("lib.agents.tools.view_image.MAX_IMAGE_BYTES", 8),
        ):
            result = await view_image.coroutine(str(IMAGE_ID), _runtime())

        assert isinstance(result, str)
        assert "too large" in result

    @pytest.mark.asyncio
    async def test_missing_file_on_disk_reports_missing(self, tmp_path):
        file = _image_file(tmp_path, file_path=str(tmp_path / "gone.png"))
        with _patched_lookup(file):
            result = await view_image.coroutine(str(IMAGE_ID), _runtime())

        assert isinstance(result, str)
        assert "missing from storage" in result


class TestRedactImageBlocks:
    def test_image_blocks_become_a_sized_note(self):
        """The bytes must not reach the persisted transcript, but the fact that
        an image was looked at, and how big it was, should."""
        encoded = base64.b64encode(b"x" * 3072).decode()
        tool_result = ToolMessage(
            content=[
                {
                    "type": "image",
                    "source_type": "base64",
                    "data": encoded,
                    "mime_type": "image/png",
                }
            ],
            tool_call_id="call-1",
            name="view_image",
        )

        (redacted,) = redact_image_blocks([tool_result])

        assert isinstance(redacted, ToolMessage)
        assert redacted.content == [
            {
                "type": "text",
                "text": "[image image/png, 3 KB; bytes omitted from the stored transcript]",
            }
        ]
        assert redacted.tool_call_id == "call-1"
        assert encoded not in str(redacted.content)

    def test_other_messages_and_text_results_pass_through_unchanged(self):
        ai = AIMessage(
            content="looking",
            tool_calls=[
                {"id": "call-1", "name": "view_image", "args": {"image_reference": "x"}}
            ],
        )
        text_result = ToolMessage(content="Error: not found", tool_call_id="call-1")
        mixed = ToolMessage(
            content=[
                {"type": "text", "text": "kept"},
                {"type": "image", "data": "QUJD"},
            ],
            tool_call_id="call-2",
        )

        out = redact_image_blocks([ai, text_result, mixed])

        assert out[0] is ai
        assert out[1] is text_result
        assert out[2].content[0] == {"type": "text", "text": "kept"}
        assert out[2].content[1]["type"] == "text"


CONVERSATION_ID = uuid.uuid4()


class TestOwnership:
    """A run reads only the images its owner holds: a project, or a conversation."""

    @pytest.mark.asyncio
    async def test_a_project_run_cannot_read_a_conversations_image(self, tmp_path):
        image = _image_file(tmp_path, project_id=None, conversation_id=CONVERSATION_ID)
        with _patched_lookup(image):
            result = await view_image.coroutine(str(IMAGE_ID), _runtime())

        assert isinstance(result, str) and result.startswith("Error: no document image")

    @pytest.mark.asyncio
    async def test_a_conversation_reads_its_own_image(self, tmp_path):
        image = _image_file(tmp_path, project_id=None, conversation_id=CONVERSATION_ID)
        tool = view_image_for_conversation(CONVERSATION_ID)
        with _patched_lookup(image):
            result = await tool.coroutine(f"draftdetective://{IMAGE_ID}?w=4&h=3")

        assert tool.name == "view_image"
        assert result[0]["data"] == base64.b64encode(PNG_BYTES).decode()

    @pytest.mark.parametrize(
        "owner",
        [
            {"project_id": None, "conversation_id": uuid.uuid4()},
            {"project_id": PROJECT_ID, "conversation_id": None},
        ],
        ids=["another conversation's", "a project's"],
    )
    @pytest.mark.asyncio
    async def test_a_conversation_cannot_read_an_image_it_does_not_own(
        self, tmp_path, owner
    ):
        with _patched_lookup(_image_file(tmp_path, **owner)):
            result = await view_image_for_conversation(CONVERSATION_ID).coroutine(
                str(IMAGE_ID)
            )

        assert isinstance(result, str) and result.startswith("Error: no document image")
