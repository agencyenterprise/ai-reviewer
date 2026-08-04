"""Tests for the tool that opens a SharePoint document from a link.

Two things carry weight here. The document must be *mounted* at ``/main.md`` rather
than returned, because a tool result over roughly 80,000 characters is evicted to a
machine-named file and every skill's line numbers are defined against ``/main.md``.
And a link must remain the only way in: there is deliberately no lookup by name, so
a name cannot reach a document the person asking could not already open.
"""

from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langgraph.types import Command

from lib.agents.tools import sharepoint
from lib.services.microsoft.graph.client import DocumentNotAllowed
from lib.services.microsoft.graph.documents import LoadedDocument


async def call(tool: Any, *args: Any) -> Any:
    """Invoke a tool's coroutine directly, bypassing its argument schema.

    The same shortcut ``test_vector_search.py`` takes. Typed loosely on purpose: the
    alternative is an ``attr-defined`` ignore at every call site, because ``@tool``
    returns a ``BaseTool`` whose ``coroutine`` mypy cannot see.
    """

    return await tool.coroutine(*args)


def mounted(result: Any) -> dict[str, Any]:
    """The files a Command mounts, having checked it is a Command that mounts some."""

    assert isinstance(result, Command), f"expected a Command, got {type(result).__name__}"
    assert result.update is not None, "a Command that updates nothing mounts nothing"
    return dict(result.update["files"])


def body_of(files: dict[str, Any], path: str) -> str:
    """A mounted file's text, joined back from the lines the vfs stores."""

    return "\n".join(files[path]["content"])


def message_of(result: Any) -> str:
    """What the model is told a Command did."""

    assert isinstance(result, Command)
    assert result.update is not None
    return str(result.update["messages"][0].content)


def runtime() -> MagicMock:
    """A tool runtime, which only needs to carry the call id."""

    fake = MagicMock()
    fake.tool_call_id = "call_abc123"
    return fake


def document(
    paragraphs: Optional[list[str]] = None,
    comments: Optional[list[tuple[str, str]]] = None,
) -> LoadedDocument:
    return LoadedDocument(
        name="v2-cern-for-ai.docx",
        url="https://x.sharepoint.com/sites/X/Shared%20Documents/v2-cern-for-ai.docx",
        paragraphs=paragraphs if paragraphs is not None else ["First.", "Second."],
        comments=comments or [],
        last_modified="2026-08-04T13:31:28Z",
        size_bytes=180097,
    )


class TestOpeningADocument:
    @pytest.mark.asyncio
    async def test_the_document_is_mounted_at_main_md(self) -> None:
        """Where every other agent and every skill expects to find it."""

        with patch.object(
            sharepoint.documents, "load", AsyncMock(return_value=document())
        ):
            result = await call(
                sharepoint.open_document, "https://x.sharepoint.com/sites/X/a.docx", runtime()
            )

        assert "/main.md" in mounted(result)

    @pytest.mark.asyncio
    async def test_the_mounted_text_carries_paragraph_numbers(self) -> None:
        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(return_value=document(["Alpha.", "Beta."])),
        ):
            result = await call(sharepoint.open_document, "https://x/a.docx", runtime())

        body = body_of(mounted(result), "/main.md")
        assert "[0] Alpha." in body and "[1] Beta." in body

    @pytest.mark.asyncio
    async def test_the_body_is_not_in_the_tool_message(self) -> None:
        """A result carrying the body would be evicted to a machine-named file."""

        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(return_value=document(["A distinctive sentence."])),
        ):
            result = await call(sharepoint.open_document, "https://x/a.docx", runtime())

        message = message_of(result)
        assert "distinctive sentence" not in message
        assert "1 paragraphs" in message and "/main.md" in message

    @pytest.mark.asyncio
    async def test_comments_are_mounted_separately_when_present(self) -> None:
        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(
                return_value=document(comments=[("Carlos", "is this right?")])
            ),
        ):
            result = await call(sharepoint.open_document, "https://x/a.docx", runtime())

        files = mounted(result)
        assert "/comments.md" in files
        assert "Carlos: is this right?" in body_of(files, "/comments.md")

    @pytest.mark.asyncio
    async def test_no_comments_means_no_comments_file(self) -> None:
        with patch.object(
            sharepoint.documents, "load", AsyncMock(return_value=document())
        ):
            result = await call(sharepoint.open_document, "https://x/a.docx", runtime())

        assert "/comments.md" not in mounted(result)

    @pytest.mark.asyncio
    async def test_a_document_outside_the_allowlist_is_refused_in_words(self) -> None:
        """The model has to be able to explain the refusal, so it gets a string."""

        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(side_effect=DocumentNotAllowed("evil.com is not allowed")),
        ):
            result = await call(
                sharepoint.open_document, "https://evil.com/a.docx", runtime()
            )

        assert isinstance(result, str)
        assert "not allowed" in result

    @pytest.mark.asyncio
    async def test_an_unexpected_failure_is_reported_not_raised(self) -> None:
        with patch.object(
            sharepoint.documents, "load", AsyncMock(side_effect=RuntimeError("boom"))
        ):
            result = await call(sharepoint.open_document, "https://x/a.docx", runtime())

        assert isinstance(result, str) and "boom" in result


class TestALinkIsTheOnlyWayIn:
    def test_there_is_no_tool_that_looks_a_document_up_by_name(self) -> None:
        """Removed on purpose, so this guards against it coming back unnoticed.

        Searching for a name means searching somewhere, and anything the service can
        search is wider than what the person asking may be allowed to read.
        """

        assert not hasattr(sharepoint, "find_document")

    def test_the_tool_tells_the_model_a_link_is_required(self) -> None:
        """Otherwise the model invents a URL when it is only given a name."""

        assert "no way to look a document up by name" in (
            sharepoint.open_document.description or ""
        )


class TestTheToolSchema:
    def test_the_runtime_is_hidden_from_the_model(self) -> None:
        """It is injected by LangChain; exposing it would invite the model to guess."""

        assert list(sharepoint.open_document.args) == ["url"]

    def test_the_tool_documents_itself(self) -> None:
        """The model picks a tool from its description, so an empty one is a bug."""

        description = sharepoint.open_document.description
        assert description and len(description) > 80
