"""Suggesting comments and tracked changes from the Word add-in's chat.

The chat runs on the server and the document is open in Word, which only the pane can
write to. So, like Teams' ``offer_changes`` (``lib/agents/tools/word_handoff.py``),
this stores what the agent would add as a handoff. The chat then shows it as a card
under the agent's message, and the pane writes it in when the person chooses Apply.

Built per turn, like the other tools of ours that act for someone: who asked, which
thread and which document are closed over, never parameters the model could change.

**Asking.** After the last batch the agent calls ``ask_to_apply``, which shows the card
and pauses the run until the person applies or dismisses it (LangGraph's
``interrupt``), then hands the agent what happened. A resumed tool runs again from its
first line, so it reads the card's outcome from the database before it would pause:
settled, it returns the outcome; still open, it pauses. Nothing the pane says is taken
as the outcome.

**One card per answer.** The agent often stores a long list in batches. The first call
that stores anything opens the answer's card; later calls in the same turn add to it, so
the person reviews and applies one card. A card that would pass its limit, or that can
no longer be changed (applying has begun), is left as it is and the batch opens a new one.
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Literal

from deepagents.backends.utils import file_data_to_string
from deepagents.middleware.filesystem import FilesystemState
from langchain.tools import BaseTool, ToolRuntime, tool
from langgraph.types import interrupt
from pydantic import BaseModel

from lib.agents.tools.word_handoff import MAX_COMMENTS, MAX_EDITS, usable_items
from lib.services.microsoft.word import chat_suggestions, handoffs
from lib.services.microsoft.word.handoffs import (
    HandoffComment,
    HandoffEdit,
    HandoffItems,
    Requester,
)
from lib.services.microsoft.word.quote_check import (
    overlapping,
    paragraph_texts,
    place,
)

logger = logging.getLogger(__name__)

# Where the open document is mounted for the agent; its quotes are checked against it.
DOCUMENT_PATH = "/documents/document.md"

NO_DOCUMENT = (
    "the document is not loaded, so no quote can be checked: answer without "
    "suggesting changes, and say they should send their message again"
)

PROBLEMS = {
    "not_found": "not in the document as quoted: copy the words exactly as they appear",
    "ambiguous": "appears in more than one paragraph: quote more words around it",
}
OVERLAPS = "shares words with another edit: make them one edit"


class SuggestionTarget(BaseModel):
    """Who the suggestions are for, and where they go."""

    requester: Requester
    chat_thread_id: uuid.UUID
    document_name: str
    document_url: str
    document_keys: list[str]


class _Card(BaseModel):
    """The card this answer's suggestions go onto."""

    id: uuid.UUID
    items: HandoffItems


def _fits(card: HandoffItems, more: HandoffItems) -> bool:
    return (
        len(card.comments) + len(more.comments) <= MAX_COMMENTS
        and len(card.edits) + len(more.edits) <= MAX_EDITS
    )


def suggest_changes_for(target: SuggestionTarget) -> BaseTool:
    """The tool, storing suggestions for ``target``, on one card per turn."""

    card: _Card | None = None
    # The model can make several calls in one message, which run at once: without this,
    # two of them could each open a card.
    lock = asyncio.Lock()

    async def store(items: HandoffItems) -> tuple[_Card, Literal["new", "added"]]:
        nonlocal card
        if card is not None and _fits(card.items, items):
            merged = usable_items(
                card.items.comments + items.comments, card.items.edits + items.edits
            )
            if await chat_suggestions.replace_items(card.id, target.requester, merged):
                card = _Card(id=card.id, items=merged)
                return card, "added"
        card_id = await handoffs.create(
            requester=target.requester,
            document_name=target.document_name,
            document_url=target.document_url,
            keys=target.document_keys,
            items=items,
            chat_thread_id=target.chat_thread_id,
        )
        card = _Card(id=card_id, items=items)
        return card, "new"

    @tool()
    async def suggest_changes(
        comments: list[HandoffComment],
        edits: list[HandoffEdit],
        runtime: ToolRuntime[Any, FilesystemState],
    ) -> str:
        """
        Suggest comments and tracked changes for the document open in Word.

        Nothing is written yet. Everything you suggest in one answer goes onto one card,
        shown when your answer ends, and is written into the document, as comments and
        tracked changes authored by Draft Detective, only if the person chooses Apply on
        it. They can also dismiss it. Calling this again in the same answer adds to that
        card, so a long list can be sent in batches.

        Each item is found in the document by its quote, so a quote must be the
        document's exact words: copied verbatim, as plain text with no markdown (no
        `**`, `#`, `|` or backslashes), within a single paragraph, and long enough to
        appear only once in the whole document.

        Args:
            comments: Points to raise, each attached to the words it is about.
            edits: Wording changes, each replacing the quoted words. Keep the quote to
                the smallest span that changes; an empty replacement deletes it.

        Every quote is checked against the document before anything is stored. If any
        is not found, or is found in more than one paragraph, nothing is stored and you
        are told which: fix those quotes, or leave those items out, and call this again.

        Returns:
            JSON saying what was stored, or why nothing was.
        """

        items = usable_items(comments, edits)
        if problems := misplaced(items, runtime.state.get("files") or {}):
            return json.dumps(
                {
                    "saved": False,
                    "message": "Nothing was saved. Fix these quotes, or leave these "
                    "items out, and call suggest_changes again with all the items.",
                    "problems": problems,
                }
            )
        if not items.count:
            return json.dumps(
                {
                    "saved": False,
                    "message": "Nothing was saved: none of those comments or edits "
                    "could be applied.",
                }
            )

        async with lock:
            before = card.items.count if card else 0
            stored, kind = await store(items)
        added = stored.items.count - (before if kind == "added" else 0)
        # Measured against what reached the card, so an edit already on it counts too.
        left_out = len(comments) + len(edits) - added
        logger.info(
            "chat %s: %s card %s, %s item(s) added",
            target.chat_thread_id,
            kind,
            stored.id,
            added,
        )
        # JSON because the pane reads the id, and whether the card is new, off this
        # result to show the card once. The agent reads it just as well.
        return json.dumps(
            {
                "saved": True,
                "suggestion_id": str(stored.id),
                "card": kind,
                "added": added,
                "comments": len(stored.items.comments),
                "edits": len(stored.items.edits),
                "message": _stored_message(kind, added, stored.items, left_out),
            }
        )

    return suggest_changes


def misplaced(items: HandoffItems, files: dict[str, Any]) -> list[str]:
    """The items whose quote the add-in would not find in exactly one paragraph.

    Without the document there is nothing to check the quotes against, so nothing is
    stored: an unchecked quote would only fail later, at Apply. The route makes sure a
    turn has the document (it asks the pane for it otherwise), so this is a safeguard.
    """

    data = files.get(DOCUMENT_PATH)
    if not isinstance(data, dict):
        return [NO_DOCUMENT]
    paragraphs = paragraph_texts(file_data_to_string(data))  # type: ignore[arg-type]  # FileData is a TypedDict
    quoted = [("comment", c.quote) for c in items.comments] + [
        ("edit", e.quote) for e in items.edits
    ]
    return [
        f"{kind} on “{quote}”: {PROBLEMS[where]}"
        for kind, quote in quoted
        if (where := place(quote, paragraphs)) != "found"
    ] + [
        f"edit on “{quote}”: {OVERLAPS}"
        for quote in overlapping([e.quote for e in items.edits], paragraphs)
    ]


def _stored_message(
    kind: Literal["new", "added"], added: int, items: HandoffItems, left_out: int
) -> str:
    holds = f"{len(items.comments)} comment(s) and {len(items.edits)} edit(s)"
    lines = [
        f"Added {added} item(s) to this answer's card, which now holds {holds}."
        if kind == "added"
        else f"Opened this answer's card with {holds}.",
        "Further suggest_changes calls in this answer add to the same card, so send "
        "any remaining items the same way. The card is shown, with Apply and Dismiss, "
        "when your answer ends; nothing is in the document until they apply it. Say "
        "briefly what you suggested.",
    ]
    if left_out:
        lines.append(
            f"{left_out} item(s) were left out: an edit that changes nothing or repeats "
            "words already suggested is dropped, and a card holds at most "
            f"{MAX_COMMENTS} comments and {MAX_EDITS} edits."
        )
    return " ".join(lines)


WAITING = {"pending", "applying"}


def ask_to_apply_for(target: SuggestionTarget) -> BaseTool:
    """The tool that shows this answer's card and waits for the person's decision."""

    @tool()
    async def ask_to_apply(suggestion_id: str) -> str:
        """
        Show your card to the person and wait until they apply or dismiss it.

        Call this once, after your last suggest_changes call of the answer, with the
        suggestion_id it returned. You get back what happened: how many items were
        applied and why any were not, or that they dismissed it. Then tell them the
        outcome. For an item that was not applied, say why; if a different quote would
        place it, you may suggest it once more and ask again.

        Args:
            suggestion_id: The suggestion_id suggest_changes returned for this answer.

        Returns:
            What became of the card.
        """

        try:
            card_id = uuid.UUID(suggestion_id)
        except ValueError:
            return "That is not a suggestion_id: pass the one suggest_changes returned."
        card = await chat_suggestions.suggestion_for(card_id, target.requester)
        if card is None or card.chat_thread_id != target.chat_thread_id:
            return "There is no card with that id in this conversation."
        if card.status in WAITING:
            # Ends the run. It resumes, and this tool runs again from the top, once the
            # person has applied or dismissed the card, so the lookup above then finds
            # it settled and the outcome is returned below.
            interrupt({"suggestion_id": str(card.id)})
            card = await chat_suggestions.suggestion_for(card_id, target.requester)
            if card is None or card.status in WAITING:
                return "The card is still waiting for them to apply or dismiss it."
        # Told now, so the next message does not report it again as news.
        await chat_suggestions.mark_heard([card.id])
        return chat_suggestions.settled_summary(card)

    return ask_to_apply
