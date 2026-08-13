"""Tests for the tool that opens a SharePoint document from a link.

Three things carry weight here. The document must be *mounted* at ``/main.md`` rather
than returned, because a tool result over roughly 80,000 characters is evicted to a
machine-named file and every skill's line numbers are defined against ``/main.md``.
A link must remain the only way in: there is deliberately no lookup by name, so a name
cannot reach a document the person asking could not already open. And the tool must
carry the identity it was built with all the way to Graph -- that token is what makes
the bot no more privileged than the asker, so losing it is a security regression
rather than a bug in a feature.
"""

from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langgraph.types import Command

from lib.agents.tools import sharepoint
from lib.services.microsoft.graph.client import DocumentNotAllowed, GraphError
from lib.services.microsoft.graph.documents import LoadedDocument


TOKEN = "a-user-token"


def opener(token: str = TOKEN) -> Any:
    """The tool as a run gets it: built for one identity."""

    return sharepoint.open_document_for(token)


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
    markdown: Optional[str] = None,
    comments: Optional[list[tuple[str, str]]] = None,
) -> LoadedDocument:
    return LoadedDocument(
        name="v2-cern-for-ai.docx",
        url="https://x.sharepoint.com/sites/X/Shared%20Documents/v2-cern-for-ai.docx",
        markdown=(
            markdown if markdown is not None else "## A heading\n\nFirst.\n\nSecond."
        ),
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
                opener(), "https://x.sharepoint.com/sites/X/a.docx", runtime()
            )

        assert "/main.md" in mounted(result)

    @pytest.mark.asyncio
    async def test_the_mounted_text_keeps_the_document_structure(self) -> None:
        """Markdown, not a flat list of paragraphs.

        Headings and tables are how the agent navigates and how a skill tells one part
        of a document from another, so losing them to a paragraph-by-paragraph read is
        the regression this guards.
        """

        markdown = (
            "## Abbreviations\n\n| AI | artificial intelligence |\n\nBody **text**."
        )
        with patch.object(
            sharepoint.documents, "load", AsyncMock(return_value=document(markdown))
        ):
            result = await call(opener(), "https://x/a.docx", runtime())

        body = body_of(mounted(result), "/main.md")
        assert body == markdown, "mounted verbatim, with nothing numbered into it"

    @pytest.mark.asyncio
    async def test_nothing_is_prefixed_onto_the_lines(self) -> None:
        """The read tool numbers lines itself, so a second scheme only competes."""

        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(return_value=document("Alpha.\n\nBeta.")),
        ):
            result = await call(opener(), "https://x/a.docx", runtime())

        body = body_of(mounted(result), "/main.md")
        assert "[0]" not in body and "[1]" not in body

    @pytest.mark.asyncio
    async def test_the_body_is_not_in_the_tool_message(self) -> None:
        """A result carrying the body would be evicted to a machine-named file."""

        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(return_value=document("A distinctive sentence.")),
        ):
            result = await call(opener(), "https://x/a.docx", runtime())

        message = message_of(result)
        assert "distinctive sentence" not in message
        assert "1 lines" in message and "/main.md" in message

    @pytest.mark.asyncio
    async def test_comments_are_mounted_separately_when_present(self) -> None:
        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(
                return_value=document(comments=[("Carlos", "is this right?")])
            ),
        ):
            result = await call(opener(), "https://x/a.docx", runtime())

        files = mounted(result)
        assert "/comments.md" in files
        assert "Carlos: is this right?" in body_of(files, "/comments.md")

    @pytest.mark.asyncio
    async def test_no_comments_clears_any_previous_ones(self) -> None:
        """A ``None`` is the reducer's delete, not an oversight.

        A conversation persists, so a second document opened in the same thread would
        otherwise inherit the first one's comments and be answered about from them.
        """

        with patch.object(
            sharepoint.documents, "load", AsyncMock(return_value=document())
        ):
            result = await call(opener(), "https://x/a.docx", runtime())

        assert mounted(result)["/comments.md"] is None

    @pytest.mark.asyncio
    async def test_a_document_outside_the_allowlist_is_refused_in_words(self) -> None:
        """The model has to be able to explain the refusal, so it gets a string."""

        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(side_effect=DocumentNotAllowed("evil.com is not allowed")),
        ):
            result = await call(
                opener(), "https://evil.com/a.docx", runtime()
            )

        assert isinstance(result, str)
        assert "not allowed" in result

    @pytest.mark.asyncio
    async def test_an_unexpected_failure_is_reported_not_raised(self) -> None:
        with patch.object(
            sharepoint.documents, "load", AsyncMock(side_effect=RuntimeError("boom"))
        ):
            result = await call(opener(), "https://x/a.docx", runtime())

        assert isinstance(result, str) and "boom" in result


class TestRememberingWhichDocumentIsOpen:
    """A mount outlives its turn, so a later turn has to know what it is looking at.

    That is what re-authorises a persisted conversation: the next question may come from
    someone else, and the document has to be re-checked against *them*. The URL is
    written with the document rather than anywhere else, so the two cannot disagree.
    """

    @pytest.mark.asyncio
    async def test_the_link_is_written_beside_the_document(self) -> None:
        url = "https://x.sharepoint.com/sites/X/a.docx"
        with patch.object(
            sharepoint.documents, "load", AsyncMock(return_value=document())
        ):
            result = await call(opener(), url, runtime())

        assert body_of(mounted(result), sharepoint.DOCUMENT_SOURCE) == url

    @pytest.mark.asyncio
    async def test_it_is_read_back_from_the_state_it_was_written_to(self) -> None:
        url = "https://x.sharepoint.com/sites/X/a.docx"
        with patch.object(
            sharepoint.documents, "load", AsyncMock(return_value=document())
        ):
            result = await call(opener(), url, runtime())

        assert sharepoint.mounted_document(mounted(result)) == url

    def test_nothing_open_means_nothing_to_re_check(self) -> None:
        assert sharepoint.mounted_document(None) is None
        assert sharepoint.mounted_document({}) is None

    def test_a_source_without_a_document_does_not_count(self) -> None:
        """Whatever produced that state, there is no mounted document to authorise."""

        files = {sharepoint.DOCUMENT_SOURCE: {"content": ["https://x/a.docx"]}}

        assert sharepoint.mounted_document(files) is None

    def test_a_document_without_a_source_does_not_count(self) -> None:
        """Fails closed: unable to name the document, so unable to re-check it.

        Reachable only from state written before the source file existed. Returning the
        URL-less document as readable would skip the check entirely, so it reads as
        "nothing mounted" and the agent opens it again from the link.
        """

        files = {"/main.md": {"content": ["[0] A."]}}

        assert sharepoint.mounted_document(files) is None

    @pytest.mark.asyncio
    async def test_a_refused_open_leaves_the_previous_document_named(self) -> None:
        """The reason the URL is not taken from the newest tool call.

        A refused open mounts nothing, so the document still loaded is the earlier one.
        Trusting the newest call would re-check a document that was never there and
        leave the mounted one unauthorised.
        """

        first = "https://x.sharepoint.com/sites/X/first.docx"
        with patch.object(
            sharepoint.documents, "load", AsyncMock(return_value=document())
        ):
            opened = mounted(await call(opener(), first, runtime()))

        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(side_effect=GraphError("could not download second.docx: 403")),
        ):
            refused = await call(
                opener(), "https://x.sharepoint.com/sites/X/second.docx", runtime()
            )

        assert isinstance(refused, str), "a refusal mounts nothing"
        assert sharepoint.mounted_document(opened) == first


class TestMountingAndUnmounting:
    """The tool and the per-turn re-read share these, so they cannot mount differently.

    Which matters most for what gets *cleared*: a thread that moves to another document,
    or gives one up, must not keep a file belonging to the previous one.
    """

    def test_a_document_without_comments_clears_a_previous_one(self) -> None:
        files = sharepoint.document_files(document(), "https://x/a.docx")

        assert files[sharepoint.COMMENTS_DOCUMENT] is None

    def test_giving_up_a_document_removes_its_source_too(self) -> None:
        """A source left behind would name a document that is no longer mounted."""

        evicted = sharepoint.evict_document()

        assert set(evicted) == {
            sharepoint.MAIN_DOCUMENT,
            sharepoint.COMMENTS_DOCUMENT,
            sharepoint.DOCUMENT_SOURCE,
        }
        assert all(value is None for value in evicted.values())

    def test_everything_a_mount_writes_can_be_unwritten(self) -> None:
        """The two have to stay in step, or a stale file survives being evicted."""

        mounted_paths = set(sharepoint.document_files(document(), "https://x/a.docx"))

        assert mounted_paths == set(sharepoint.evict_document())


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
            opener().description or ""
        )


class TestWhoseAccessIsUsed:
    """The token the tool was built with is what limits what a run can read.

    Under Teams SSO it is the asker's, so Graph refuses a document they cannot open.
    If it were dropped anywhere between the tool and Graph, every read would silently
    become the service's -- which is the privilege this whole arrangement removes, and
    it would fail open rather than closed.
    """

    @pytest.mark.asyncio
    async def test_the_token_reaches_the_loader(self) -> None:
        load = AsyncMock(return_value=document())
        with patch.object(sharepoint.documents, "load", load):
            await call(opener("carlos-token"), "https://x/a.docx", runtime())

        assert load.await_args is not None
        assert load.await_args.kwargs["token"] == "carlos-token"

    @pytest.mark.asyncio
    async def test_two_tools_do_not_share_an_identity(self) -> None:
        """One process serves many askers, so the binding has to be per tool."""

        load = AsyncMock(return_value=document())
        with patch.object(sharepoint.documents, "load", load):
            await call(opener("first-user"), "https://x/a.docx", runtime())
            await call(opener("second-user"), "https://x/a.docx", runtime())

        used = [call_.kwargs["token"] for call_ in load.await_args_list]
        assert used == ["first-user", "second-user"]

    @pytest.mark.asyncio
    async def test_a_refusal_for_this_user_is_explained_not_retried(self) -> None:
        """Graph answers 403 when the asker cannot open it. That is the check working."""

        with patch.object(
            sharepoint.documents,
            "load",
            AsyncMock(side_effect=GraphError("could not download a.docx: 403")),
        ):
            result = await call(opener(), "https://x/a.docx", runtime())

        assert isinstance(result, str) and "403" in result

    def test_the_model_is_told_it_reads_as_the_asker(self) -> None:
        """So a refusal is reported rather than worked around."""

        assert "as the person who asked" in (opener().description or "")


class TestTheToolSchema:
    def test_the_runtime_and_the_token_are_hidden_from_the_model(self) -> None:
        """The runtime is injected by LangChain; the token is closed over.

        Neither belongs in the schema. A token the model could see is a token it could
        put in an answer.
        """

        assert list(opener().args) == ["url"]

    def test_the_tool_documents_itself(self) -> None:
        """The model picks a tool from its description, so an empty one is a bug."""

        description = opener().description
        assert description and len(description) > 80
        assert TOKEN not in description
