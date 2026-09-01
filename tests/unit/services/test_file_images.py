"""Unit tests for `lib.services.file_images`."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.sql.dml import Delete

from lib.models.file import FileRole
from lib.services.file_images import replace_extracted_images
from lib.services.image_extraction import ExtractedImage

MODULE = "lib.services.file_images"


class _FakeSession:
    def __init__(self):
        self.executed: list = []
        self.added: list = []
        self.committed = False

    async def execute(self, stmt):
        self.executed.append(stmt)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


def _parent() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        uploaded_by=uuid.uuid4(),
        revision=3,
    )


def _extracted(alt: str = "") -> ExtractedImage:
    return ExtractedImage(
        image_path="/uploads/extracted_images/abc.png",
        mime_type="image/png",
        file_size=123,
        content_hash="abc",
        line_number=7,
        alt=alt,
    )


@pytest.mark.asyncio
async def test_replaces_rows_and_inherits_parent_fields():
    parent = _parent()
    session = _FakeSession()
    images = [_extracted(alt="Figure 1"), _extracted()]

    with (
        patch(f"{MODULE}.get_file_by_id", new=AsyncMock(return_value=parent)),
        patch(f"{MODULE}.get_async_db_session", return_value=session),
    ):
        await replace_extracted_images(parent.id, images)

    # Old rows for this parent are deleted before the new ones go in, so a
    # reconversion never leaves stale images behind.
    assert len(session.executed) == 1
    assert isinstance(session.executed[0], Delete)
    assert "parent_file_id" in str(session.executed[0])

    assert [f.id for f in session.added] == [images[0].id, images[1].id]
    assert [f.file_name for f in session.added] == ["image-1.png", "image-2.png"]
    for row in session.added:
        assert row.role == FileRole.EXTRACTED_IMAGE
        assert row.parent_file_id == parent.id
        assert row.project_id == parent.project_id
        assert row.uploaded_by == parent.uploaded_by
        assert row.revision == parent.revision
        assert row.file_path == "/uploads/extracted_images/abc.png"
        assert row.file_type == "image/png"
        assert row.content_hash == "abc"
    # Alt text lands in description; empty alt stays NULL.
    assert [f.description for f in session.added] == ["Figure 1", None]
    assert session.committed


@pytest.mark.asyncio
async def test_no_images_still_clears_previous_rows():
    parent = _parent()
    session = _FakeSession()

    with (
        patch(f"{MODULE}.get_file_by_id", new=AsyncMock(return_value=parent)),
        patch(f"{MODULE}.get_async_db_session", return_value=session),
    ):
        await replace_extracted_images(parent.id, [])

    assert isinstance(session.executed[0], Delete)
    assert session.added == []
    assert session.committed
