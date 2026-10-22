"""Chat usage behind the admin dashboard: the web app's /chat, Word and Teams.

Every conversation on any surface has a row in ``conversations`` saying which
surface it is on (``lib/models/conversation.py``), which is where conversations
started are counted. What was said is only in the LangGraph checkpointer, so
messages are counted there: LangGraph writes one checkpoint with
``metadata.source = 'input'`` each time a graph is given new input, and none
when a run resumes after an interrupt (the Word chat resuming once a suggestion
is applied). On the root namespace that is one per message a person sent.

The checkpoint's metadata also carries the run config's ``langfuse_user_id``,
which each surface sets to whoever sent that message: the user's id on /chat,
the Microsoft account's object id in Word, the sender's name in Teams. It is
the only record of who sent a message in a Teams conversation, which belongs to
everyone in it, so people are counted from it on every surface alike.

The checkpoint thread is the conversation's id, except in Teams, where it is
the id Teams gives the conversation (``microsoft_teams_conversations``).
"""

import uuid
from collections.abc import Collection
from datetime import date, datetime

from sqlalchemy import (
    DateTime,
    Select,
    String,
    Text,
    and_,
    cast,
    column,
    distinct,
    func,
    select,
    table,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import col

from lib.models.conversation import Conversation, ConversationKind
from lib.models.microsoft_teams_conversation import MicrosoftTeamsConversation
from lib.services.admin_dashboard.models import (
    ChatActivityPoint,
    ChatSurfaceUsage,
    MetricWithDelta,
)
from lib.services.admin_dashboard.queries import (
    _bucket_starts,
    _current_and_previous_counts,
    _in_current,
    _in_previous,
    _user_not_ignored,
)
from lib.services.admin_dashboard.window import DashboardWindow

# LangGraph's own table, created by ``AsyncPostgresSaver.setup()`` rather than
# by a model here, so described only as far as these queries read it.
_checkpoints = table(
    "checkpoints",
    column("thread_id", String),
    column("checkpoint_ns", String),
    column("checkpoint", JSONB),
    column("metadata", JSONB),
)

_SURFACES = list(ConversationKind)


async def _has_checkpoints(session: AsyncSession) -> bool:
    """Whether LangGraph has made its tables yet.

    It makes them the first time any agent keeps a thread, so a deployment
    nobody has chatted on has none, and querying them would fail the page.
    """
    found = await session.execute(text("SELECT to_regclass('checkpoints')"))
    return found.scalar() is not None


def _sent_at() -> ColumnElement[datetime]:
    """When the message was sent: the input checkpoint's own timestamp."""
    return cast(_checkpoints.c.checkpoint["ts"].astext, DateTime(timezone=True))


def _messages_from(
    window: DashboardWindow, ignored: Collection[uuid.UUID]
) -> Select[tuple[()]]:
    """Input checkpoints since `previous_start`, joined to their conversation.

    Driven from ``conversations`` so the checkpoints are reached through their
    ``thread_id`` index: the table also holds every other agent's threads, and
    is far too large to scan for a dashboard.
    """
    thread_id = func.coalesce(
        col(MicrosoftTeamsConversation.teams_conversation_id),
        cast(col(Conversation.id), Text),
    )
    return (
        select()
        .select_from(Conversation)
        .outerjoin(
            MicrosoftTeamsConversation,
            col(MicrosoftTeamsConversation.id) == col(Conversation.id),
        )
        .join(
            _checkpoints,
            and_(
                _checkpoints.c.thread_id == thread_id,
                _checkpoints.c.checkpoint_ns == "",
                _checkpoints.c.metadata["source"].astext == "input",
            ),
        )
        .where(
            _sent_at() >= window.previous_start,
            _user_not_ignored(col(Conversation.user_id), ignored),
        )
    )


async def get_chat_surfaces(
    session: AsyncSession,
    window: DashboardWindow,
    ignored_user_ids: Collection[uuid.UUID] = (),
) -> list[ChatSurfaceUsage]:
    """Per surface: conversations started, messages sent, and who sent them.

    Every surface is listed, in a fixed order, used or not.
    """
    kind = col(Conversation.kind)
    created_at = col(Conversation.created_at)
    started, started_before = _current_and_previous_counts(window, created_at)
    started_stmt = (
        select(kind, started, started_before)
        .where(
            created_at >= window.previous_start,
            _user_not_ignored(col(Conversation.user_id), ignored_user_ids),
        )
        .group_by(kind)
    )

    started_by_kind = {
        row[0]: (row[1], row[2]) for row in (await session.execute(started_stmt))
    }
    messages_by_kind: dict[str, tuple[int, int, int]] = {}
    if await _has_checkpoints(session):
        messages_by_kind = await _messages_by_kind(session, window, ignored_user_ids)

    surfaces: list[ChatSurfaceUsage] = []
    for surface in _SURFACES:
        started_now, started_then = started_by_kind.get(surface.value, (0, 0))
        sent_now, sent_then, people = messages_by_kind.get(surface.value, (0, 0, 0))
        surfaces.append(
            ChatSurfaceUsage(
                surface=surface,
                conversations_started=MetricWithDelta(
                    current=started_now, previous=started_then
                ),
                messages=MetricWithDelta(current=sent_now, previous=sent_then),
                people=people,
            )
        )
    return surfaces


async def _messages_by_kind(
    session: AsyncSession,
    window: DashboardWindow,
    ignored_user_ids: Collection[uuid.UUID],
) -> dict[str, tuple[int, int, int]]:
    """Messages in this window and the last, and senders in this one, per kind."""
    kind = col(Conversation.kind)
    sent_at = _sent_at()
    sender = _checkpoints.c.metadata["langfuse_user_id"].astext
    messages_stmt = (
        _messages_from(window, ignored_user_ids)
        .add_columns(
            kind,
            func.count().filter(_in_current(window, sent_at)),
            func.count().filter(_in_previous(window, sent_at)),
            func.count(distinct(sender)).filter(_in_current(window, sent_at)),
        )
        .group_by(kind)
    )
    return {
        row[0]: (row[1], row[2], row[3])
        for row in (await session.execute(messages_stmt))
    }


async def get_chat_activity(
    session: AsyncSession,
    window: DashboardWindow,
    ignored_user_ids: Collection[uuid.UUID] = (),
) -> list[ChatActivityPoint]:
    """Messages sent per bucket, per surface, with no holes in the series.

    Bucketed in UTC for the same reason as the assessment series
    (``queries.get_activity``).
    """
    sent_at = _sent_at()
    kind = col(Conversation.kind)
    bucket = func.date_trunc(window.granularity.value, func.timezone("UTC", sent_at))
    stmt = (
        _messages_from(window, ignored_user_ids)
        .add_columns(bucket, kind, func.count())
        .where(_in_current(window, sent_at))
        .group_by(bucket, kind)
    )

    counts: dict[tuple[date, str], int] = {}
    if await _has_checkpoints(session):
        counts = {
            (row[0].date(), row[1]): row[2] for row in (await session.execute(stmt))
        }
    return [
        ChatActivityPoint(
            bucket=day,
            web=counts.get((day, ConversationKind.WEB.value), 0),
            word=counts.get((day, ConversationKind.WORD.value), 0),
            teams=counts.get((day, ConversationKind.TEAMS.value), 0),
        )
        for day in _bucket_starts(window)
    ]
