"""Opening a SharePoint document mid-run.

An agent answering a question from Teams is not told which document to read, so it
opens one itself from a link in the message.

Only from a link. Finding a document by name was built and removed: matching names
means searching somewhere, and anything the service can search is wider than what the
person asking may be allowed to read. A link is something they already had.

The tool is built per run, bound to one identity, by ``open_document_for(token)``.
That is deliberate: the token belongs to the person who asked, so a run cannot read
anything they could not, and there is no module-level tool that would read as the
service instead. The model never sees the token -- it is closed over, not a parameter.

``open_document`` mounts the document at ``/main.md`` rather than returning its text.
Two reasons, and the second is the one that decides it:

- ``/main.md`` is the path every other agent and skill in this codebase reads. The
  line numbers in ``skills/issues/SKILL.md`` are *defined* relative to it.
- A tool result over roughly 80,000 characters is evicted by the filesystem
  middleware to ``/large_tool_results/{tool_call_id}``. Real documents here run to
  that size, so returning the body would scatter it to a machine-generated path
  instead of the one the skills expect.

A mount outlives its turn once a conversation is checkpointed, so the link is written
beside it at ``DOCUMENT_SOURCE``: that is how a later turn knows what to re-read, and as
whom.
"""

import logging
from typing import Any, Optional

from deepagents.backends.utils import create_file_data
from deepagents.middleware.filesystem import FilesystemState
from langchain.tools import BaseTool, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from lib.agents.deep_agent_setup import number_paragraphs
from lib.services.microsoft.graph import documents
from lib.services.microsoft.graph.client import (
    DocumentNotAllowed,
    GraphError,
    redacted,
)

logger = logging.getLogger(__name__)

MAIN_DOCUMENT = "/main.md"
COMMENTS_DOCUMENT = "/comments.md"

# Which document is at MAIN_DOCUMENT, written beside it rather than in a table that could
# drift out of step with what is actually mounted.
DOCUMENT_SOURCE = "/main.source"


def open_document_for(token: str) -> BaseTool:
    """The document-opening tool, reading as whoever ``token`` belongs to.

    A factory rather than a module-level tool so the identity is chosen per run and
    cannot be omitted. Under a Teams SSO token this is what makes the bot no more
    privileged than the person who asked: Graph refuses a document they cannot open,
    and the refusal comes back as something the agent explains.
    """

    @tool()
    async def open_document(
        url: str, runtime: ToolRuntime[Any, FilesystemState]
    ) -> Command | str:
        """
        Open a Word document so you can read it. Do this before answering about one.

        The document becomes available at /main.md, with every paragraph prefixed by
        its number like [12]. Any comments already on it become available at
        /comments.md. Use your read and search tools on those files; this tool does
        not return the text.

        You open it as the person who asked, so a document they cannot access will be
        refused. Tell them that plainly rather than trying another way in.

        Args:
            url: The document's SharePoint link, as pasted by the person asking. There
                is no way to look a document up by name; without a link, ask for one.

        Returns:
            A confirmation of what was opened. Example:
            Opened 'v2-04-21-2025- cern-for-ai-for-full-review.docx' at /main.md:
            366 paragraphs, 4 comments at /comments.md. Modified 2026-08-04T13:31:28Z.
        """

        try:
            document = await documents.load(url, token=token)
        except DocumentNotAllowed as error:
            return f"I am not allowed to read that document: {error}"
        except GraphError as error:
            logger.error("could not open %s: %s", redacted(url), error)
            return f"I could not open that document: {error}"
        except Exception as error:  # noqa: BLE001 - the model decides what to do next
            logger.exception("could not open %s", redacted(url))
            return f"I could not open that document: {error}"

        # A Command is how a tool writes into the agent's filesystem; the built-in
        # write_file does the same. The files key merges, so this adds rather than
        # replaces, and mounting the same path twice overwrites it.
        return Command(
            update={
                "files": document_files(document, url),
                "messages": [
                    ToolMessage(
                        content=describe(document),
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )

    return open_document


def document_files(document: documents.LoadedDocument, url: str) -> dict[str, Any]:
    """A document as the agent's filesystem holds it.

    Shared by the tool and by the per-turn re-read, so the two cannot mount a document
    differently -- what needs clearing is not obvious from either call site alone.
    """

    return {
        MAIN_DOCUMENT: create_file_data(number_paragraphs(document.paragraphs)),
        # Written with the document, never separately, so that a later turn can name what
        # it is holding and re-read it as whoever is asking then.
        DOCUMENT_SOURCE: create_file_data(url),
        # Comments are cleared when there are none rather than left out: a thread that
        # opens a second document would otherwise keep answering from the first one's.
        COMMENTS_DOCUMENT: (
            create_file_data(format_comments(document.comments))
            if document.comments
            else None
        ),
    }


def evict_document() -> dict[str, None]:
    """Deletion markers for every file a document mounts.

    ``None`` is how the filesystem reducer spells a delete. The source goes with the
    body, or it would name a document that is no longer there.
    """

    return {MAIN_DOCUMENT: None, COMMENTS_DOCUMENT: None, DOCUMENT_SOURCE: None}


def mounted_document(files: Optional[dict[str, Any]]) -> Optional[str]:
    """The URL of the document currently mounted at ``MAIN_DOCUMENT``, if any.

    Read from ``DOCUMENT_SOURCE`` rather than from the newest ``open_document`` call: a
    refused open writes nothing, so the newest call can name a document that was never
    loaded while the previous one is still mounted.
    """

    if not files:
        return None
    source = files.get(DOCUMENT_SOURCE)
    if not source or MAIN_DOCUMENT not in files:
        return None
    url = "\n".join(source.get("content") or []).strip()
    return url or None


def format_comments(comments: list[tuple[str, str]]) -> str:
    """The document's existing comments, as a file the agent can read."""

    return "\n\n".join(f"{author}: {text}" for author, text in comments)


def describe(document: documents.LoadedDocument) -> str:
    """What was opened, without any of its content.

    Kept to a summary on purpose: a tool result carrying the body would be evicted
    to a machine-named file and defeat the mounting above.
    """

    parts = [
        f"Opened '{document.name}' at {MAIN_DOCUMENT}: "
        f"{len(document.paragraphs)} paragraphs"
    ]
    if document.comments:
        parts.append(f", {len(document.comments)} comments at {COMMENTS_DOCUMENT}")
    parts.append(".")
    if document.last_modified:
        parts.append(f" Modified {document.last_modified}.")
    return "".join(parts)
