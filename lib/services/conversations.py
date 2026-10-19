"""Starting conversations, and finding a Teams conversation's.

Every surface's conversation has a row in ``conversations`` (``lib/models/conversation.py``)
with the same id as the surface's own row, so the two are created together: the shared
row first, flushed, then the surface's, in the caller's transaction.
"""

import uuid
from collections.abc import Awaitable, Callable

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from lib.config.database import get_async_db_session
from lib.models.conversation import Conversation, ConversationKind
from lib.models.microsoft_teams_conversation import MicrosoftTeamsConversation

# Who a conversation is listed under, asked only when one is started: finding the user
# can mean a database write, or a Graph call for a Teams asker.
Starter = Callable[[], Awaitable[uuid.UUID | None]]


async def start(
    session: AsyncSession, kind: ConversationKind, user_id: uuid.UUID | None = None
) -> uuid.UUID:
    """A new conversation's id, its shared row added to ``session`` and flushed."""

    conversation = Conversation(id=uuid.uuid4(), kind=kind, user_id=user_id)
    session.add(conversation)
    # The surface's row points at this one, so it has to exist first.
    await session.flush()
    return conversation.id


async def remove(session: AsyncSession, conversation_id: uuid.UUID) -> None:
    """Delete a conversation; its surface's row and its files go with it (cascade)."""

    await session.execute(
        delete(Conversation).where(col(Conversation.id) == conversation_id)
    )


async def _teams(teams_conversation_id: str) -> uuid.UUID | None:
    async with get_async_db_session() as session:
        return (
            await session.execute(
                select(col(MicrosoftTeamsConversation.id)).where(
                    col(MicrosoftTeamsConversation.teams_conversation_id)
                    == teams_conversation_id
                )
            )
        ).scalar_one_or_none()


async def for_teams(
    teams_conversation_id: str, starter: Starter | None = None
) -> uuid.UUID:
    """The conversation for a Teams conversation id, started on its first question.

    ``starter`` names the user it is listed under, asked only when the conversation is
    started: the person who asked first. Two questions in a new conversation can arrive
    at once, on different workers: the unique Teams id lets only one start it, and the
    other reads back the winner's.
    """

    if (found := await _teams(teams_conversation_id)) is not None:
        return found
    user_id = await starter() if starter else None
    try:
        async with get_async_db_session() as session:
            conversation_id = await start(session, ConversationKind.TEAMS, user_id)
            session.add(
                MicrosoftTeamsConversation(
                    id=conversation_id, teams_conversation_id=teams_conversation_id
                )
            )
            await session.commit()
            return conversation_id
    except IntegrityError:
        if (found := await _teams(teams_conversation_id)) is not None:
            return found
        raise
