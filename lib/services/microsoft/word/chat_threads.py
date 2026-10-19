"""The add-in chat's threads: one current conversation per account and document.

Scoped like handoffs, to the Microsoft account the pane is signed in as (its Entra
object id, and its tenant when known), never to an email address. A thread is found by
the document's URL the way handoffs are: Word reports different URL forms in different
clients, so a thread stores every key its URL yields and matches on any of them.

Clearing a chat stamps the thread rather than deleting it. The next message then starts
a new thread, and the old conversation stays in the checkpointer, out of the pane's reach.
"""

import uuid
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse

from sqlalchemy import and_, or_, select, update
from sqlmodel import col

from lib.config.database import get_async_db_session
from lib.models.conversation import ConversationKind
from lib.models.microsoft_word_chat_thread import MicrosoftWordChatThread
from lib.services import conversations
from lib.services.microsoft.word.handoffs import Account, keys_for_url

# A document never saved has no URL. The pane sends a key of its own instead,
# ``unsaved:<id>`` (``chatDocumentKey`` in ``frontend/lib/addin/pane-document.ts``), so
# each unsaved document gets its own conversation. ``UNSAVED`` is only for a pane that
# sends nothing at all.
UNSAVED = "unsaved"
PANE_KEY_PREFIX = "unsaved:"


def thread_keys(url: str) -> list[str]:
    """The keys a thread for the document at ``url`` is stored and found under."""

    if keys := keys_for_url(url):
        return sorted(keys)
    url = url.strip()
    return [f"url:{url.lower()}"] if url else [UNSAVED]


def document_name(url: str) -> str:
    """A name for the document, from its URL. Word gives the pane nothing better."""

    if url.startswith(PANE_KEY_PREFIX):
        return "this document"
    name = PurePosixPath(unquote(urlparse(url).path)).name
    return name or "this document"


def _owned_by(account: Account) -> Any:
    mine = col(MicrosoftWordChatThread.owner_oid) == account.oid
    if not account.tid:
        return mine
    return and_(
        mine,
        or_(
            col(MicrosoftWordChatThread.owner_tid).is_(None),
            col(MicrosoftWordChatThread.owner_tid) == account.tid,
        ),
    )


async def current(account: Account, url: str) -> MicrosoftWordChatThread | None:
    """The account's uncleared thread for this document, the newest if several."""

    wanted = set(thread_keys(url))
    async with get_async_db_session() as session:
        rows = await session.execute(
            select(MicrosoftWordChatThread)
            .where(_owned_by(account))
            .where(col(MicrosoftWordChatThread.cleared_at).is_(None))
            .order_by(col(MicrosoftWordChatThread.last_turn_at).desc())
        )
        threads = list(rows.scalars().all())
    return next((t for t in threads if wanted & set(t.document_keys)), None)


async def current_or_new(
    account: Account, url: str, starter: conversations.Starter | None = None
) -> MicrosoftWordChatThread:
    """The current thread for this document, starting one if there is none.

    ``starter`` names the user a new thread is listed under, asked only when one starts.
    """

    if (thread := await current(account, url)) is not None:
        return thread
    user_id = await starter() if starter else None
    now = datetime.now(UTC)
    async with get_async_db_session() as session:
        thread = MicrosoftWordChatThread(
            id=await conversations.start(session, ConversationKind.WORD, user_id),
            owner_oid=account.oid,
            owner_tid=account.tid,
            document_name=document_name(url),
            document_url=url,
            document_keys=thread_keys(url),
            created_at=now,
            last_turn_at=now,
        )
        session.add(thread)
        await session.commit()
        await session.refresh(thread)
    return thread


async def begin_turn(thread_id: uuid.UUID) -> datetime | None:
    """Stamp a new turn, and return when the previous one began.

    Suggestions settled since then are news to the agent. A new thread's "previous
    turn" is its creation, so nothing counts as news on its first message.
    """

    async with get_async_db_session() as session:
        thread = await session.get(MicrosoftWordChatThread, thread_id)
        if thread is None:
            return None
        previous = thread.last_turn_at
        thread.last_turn_at = datetime.now(UTC)
        session.add(thread)
        await session.commit()
    return previous


async def clear(account: Account, url: str) -> bool:
    """Set the current thread aside, so the next message starts afresh.

    False when there was nothing to clear.
    """

    thread = await current(account, url)
    if thread is None:
        return False
    async with get_async_db_session() as session:
        await session.execute(
            update(MicrosoftWordChatThread)
            .where(col(MicrosoftWordChatThread.id) == thread.id)
            .where(_owned_by(account))
            .values(cleared_at=datetime.now(UTC))
        )
        await session.commit()
    return True
