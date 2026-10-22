"""Integration tests for the dashboard's chat figures, on real Postgres.

The figures are global and other tests write conversations in parallel, so
each assertion compares two readings taken in one snapshot: everyone, and
everyone but the fixture's user. Every conversation here is listed under that
user, so the difference is exactly the fixture's rows. Teams messages are the
exception, since the ignore list never applies to them: they are compared
with a reading taken after deleting them in a transaction that is rolled back.

The checkpoints are written by hand, shaped as LangGraph writes them: what is
pinned is which of them count as a message, and that a Teams conversation's
are found under the id Teams gives it.
"""

import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
import pytest_asyncio
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from lib.agents.checkpointer import SETUP_LOCK_KEY
from lib.config.database import get_async_db_session
from lib.config.env import config
from lib.models.conversation import Conversation, ConversationKind
from lib.models.microsoft_teams_conversation import MicrosoftTeamsConversation
from lib.models.user import User, UserRole
from lib.services.admin_dashboard import chat_queries
from lib.services.admin_dashboard.models import ChatActivityPoint, ChatSurfaceUsage
from lib.services.admin_dashboard.window import DashboardWindow

NOW = datetime.now(UTC)
DAYS = 7


class _Fixture:
    def __init__(self, user: User, teams_id: str):
        self.user = user
        self.teams_id = teams_id


async def _create_checkpoint_tables() -> None:
    """LangGraph's tables, which the app creates on first use, not by migration."""
    async with await psycopg.AsyncConnection.connect(
        config.DATABASE_URL, autocommit=True, row_factory=dict_row
    ) as conn:
        await conn.execute("SELECT pg_advisory_lock(%s)", (SETUP_LOCK_KEY,))
        try:
            await AsyncPostgresSaver(conn=conn).setup()
        finally:
            await conn.execute("SELECT pg_advisory_unlock(%s)", (SETUP_LOCK_KEY,))


async def _checkpoint(
    session: AsyncSession,
    thread_id: str,
    at: datetime,
    *,
    source: str = "input",
    sender: str = "someone",
    namespace: str = "",
) -> None:
    metadata = {"source": source, "step": -1, "langfuse_user_id": sender}
    await session.execute(
        text(
            "INSERT INTO checkpoints (thread_id, checkpoint_ns, checkpoint_id, "
            "checkpoint, metadata) VALUES (:thread, :ns, :id, "
            "CAST(:checkpoint AS jsonb), CAST(:metadata AS jsonb))"
        ),
        {
            "thread": thread_id,
            "ns": namespace,
            "id": str(uuid.uuid4()),
            "checkpoint": json.dumps({"ts": at.isoformat()}),
            "metadata": json.dumps(metadata),
        },
    )


@pytest_asyncio.fixture
async def chat_data() -> AsyncIterator[_Fixture]:
    """One conversation per surface, all listed under one user.

    The web conversation has two messages this week from its owner, one from
    the week before, a resume (`loop`) and a subgraph's input, which are not
    messages. The Word one has one message. The Teams one, which the user
    started, has two, from two other people, under its Teams id.
    """
    await _create_checkpoint_tables()
    tag = uuid.uuid4().hex[:12]
    user = User(
        id=uuid.uuid4(),
        email=f"chat-dash-{tag}@example.com",
        name=f"Chat {tag}",
        role=UserRole.USER,
        show_experimental_features=False,
    )
    web, word, teams = (
        Conversation(id=uuid.uuid4(), kind=kind, user_id=user.id, created_at=NOW)
        for kind in (
            ConversationKind.WEB,
            ConversationKind.WORD,
            ConversationKind.TEAMS,
        )
    )
    teams_id = f"19:{tag}@thread.v2;messageid=1"
    async with get_async_db_session() as session:
        session.add(user)
        await session.flush()
        session.add_all([web, word, teams])
        await session.flush()
        session.add(
            MicrosoftTeamsConversation(id=teams.id, teams_conversation_id=teams_id)
        )
        hour_ago = NOW - timedelta(hours=1)
        await _checkpoint(session, str(web.id), hour_ago, sender=str(user.id))
        await _checkpoint(session, str(web.id), hour_ago, sender=str(user.id))
        await _checkpoint(
            session, str(web.id), NOW - timedelta(days=DAYS + 1), sender=str(user.id)
        )
        await _checkpoint(session, str(web.id), hour_ago, source="loop")
        await _checkpoint(session, str(web.id), hour_ago, namespace="tools:abc")
        await _checkpoint(session, str(word.id), hour_ago, sender="oid-ana")
        # Names no parallel fixture shares, so each is one more person.
        await _checkpoint(session, teams_id, hour_ago, sender=f"Ana {tag}")
        await _checkpoint(session, teams_id, hour_ago, sender=f"Bo {tag}")
        await session.commit()

    yield _Fixture(user, teams_id)

    threads = [str(web.id), str(word.id), teams_id]
    async with get_async_db_session() as session:
        await session.execute(
            text("DELETE FROM checkpoints WHERE thread_id = ANY(:threads)"),
            {"threads": threads},
        )
        await session.execute(
            delete(Conversation).where(col(Conversation.user_id) == user.id)
        )
        await session.execute(delete(User).where(col(User.id) == user.id))
        await session.commit()


def _by_surface(
    surfaces: list[ChatSurfaceUsage],
) -> dict[ConversationKind, ChatSurfaceUsage]:
    return {surface.surface: surface for surface in surfaces}


async def _with_and_without(
    user: User,
) -> tuple[
    dict[ConversationKind, ChatSurfaceUsage],
    dict[ConversationKind, ChatSurfaceUsage],
    list[ChatActivityPoint],
    list[ChatActivityPoint],
]:
    """Both readings, surfaces and activity, from one snapshot."""
    window = DashboardWindow.for_days(DAYS)
    async with get_async_db_session() as session:
        await session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        everyone = await chat_queries.get_chat_surfaces(session, window)
        others = await chat_queries.get_chat_surfaces(session, window, [user.id])
        activity = await chat_queries.get_chat_activity(session, window)
        others_activity = await chat_queries.get_chat_activity(
            session, window, [user.id]
        )
    return _by_surface(everyone), _by_surface(others), activity, others_activity


@pytest.mark.asyncio
async def test_messages_are_counted_per_surface(chat_data: _Fixture) -> None:
    everyone, others, _, _ = await _with_and_without(chat_data.user)

    def mine(kind: ConversationKind) -> tuple[int, int, int, int]:
        a, b = everyone[kind], others[kind]
        return (
            a.conversations_started.current - b.conversations_started.current,
            a.messages.current - b.messages.current,
            a.messages.previous - b.messages.previous,
            a.people - b.people,
        )

    assert list(everyone) == [
        ConversationKind.WEB,
        ConversationKind.WORD,
        ConversationKind.TEAMS,
    ]
    # Web: the resume and the subgraph's input are not messages.
    assert mine(ConversationKind.WEB) == (1, 2, 1, 1)
    assert mine(ConversationKind.WORD) == (1, 1, 0, 1)
    # Teams: the conversation is listed under the ignored user, who started it,
    # but its messages are Ana's and Bo's, so they stay.
    assert mine(ConversationKind.TEAMS) == (1, 0, 0, 0)


@pytest.mark.asyncio
async def test_teams_messages_are_found_under_the_teams_id(
    chat_data: _Fixture,
) -> None:
    window = DashboardWindow.for_days(DAYS)
    async with get_async_db_session() as session:
        await session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        before = _by_surface(await chat_queries.get_chat_surfaces(session, window))
        await session.execute(
            text("DELETE FROM checkpoints WHERE thread_id = :thread"),
            {"thread": chat_data.teams_id},
        )
        after = _by_surface(await chat_queries.get_chat_surfaces(session, window))
        await session.rollback()

    teams_before, teams_after = (
        before[ConversationKind.TEAMS],
        after[ConversationKind.TEAMS],
    )
    assert teams_before.messages.current - teams_after.messages.current == 2
    assert teams_before.people - teams_after.people == 2


@pytest.mark.asyncio
async def test_the_activity_series_counts_the_same_messages(
    chat_data: _Fixture,
) -> None:
    _, _, activity, others = await _with_and_without(chat_data.user)

    assert len(activity) == len(others) >= DAYS
    assert sum(point.web for point in activity) - sum(p.web for p in others) == 2
    assert sum(point.word for point in activity) - sum(p.word for p in others) == 1
    assert sum(point.teams for point in activity) == sum(p.teams for p in others)


@pytest.mark.asyncio
async def test_without_langgraphs_tables_there_are_no_messages_yet() -> None:
    """A deployment nobody has chatted on has no `checkpoints` table at all.

    Seen from a session whose search path holds only its own empty copies of
    the conversation tables, rather than by dropping `checkpoints`, which would
    pull it from under the tests running alongside.
    """
    window = DashboardWindow.for_days(DAYS)
    async with get_async_db_session() as session:
        for name in ("conversations", "microsoft_teams_conversations"):
            await session.execute(
                text(f"CREATE TEMP TABLE {name} (LIKE public.{name})")
            )
        await session.execute(text("SET LOCAL search_path = pg_temp"))

        surfaces = await chat_queries.get_chat_surfaces(session, window)
        activity = await chat_queries.get_chat_activity(session, window)
        await session.rollback()

    assert [surface.messages.current for surface in surfaces] == [0, 0, 0]
    assert all(point.web == point.word == point.teams == 0 for point in activity)
