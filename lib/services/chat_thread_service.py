"""Business logic for persisted assistant-ui chat threads and messages.

Each thread and message belongs to a user; all reads and writes are scoped to
the requesting user, and cross-user access raises 404.
"""

import uuid
from datetime import datetime
from typing import Any, Optional, Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from lib.config.database import get_async_db_session
from lib.models.chat_thread import ChatMessage, ChatThread
from lib.models.user import User


async def list_threads(user: User) -> Sequence[ChatThread]:
    async with get_async_db_session() as session:
        stmt = (
            select(ChatThread)
            .where(col(ChatThread.user_id) == user.id)
            .order_by(col(ChatThread.last_updated_at).desc())
        )
        return list((await session.execute(stmt)).scalars().all())


async def create_thread(user: User, title: Optional[str] = None) -> ChatThread:
    async with get_async_db_session() as session:
        thread = ChatThread(user_id=user.id, title=title)
        session.add(thread)
        await session.commit()
        await session.refresh(thread)
        return thread


async def _get_owned_thread(
    session: AsyncSession, thread_id: uuid.UUID, user: User
) -> ChatThread:
    stmt = select(ChatThread).where(
        col(ChatThread.id) == thread_id, col(ChatThread.user_id) == user.id
    )
    thread = (await session.execute(stmt)).scalar_one_or_none()
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


async def get_thread(thread_id: uuid.UUID, user: User) -> ChatThread:
    async with get_async_db_session() as session:
        return await _get_owned_thread(session, thread_id, user)


async def rename_thread(thread_id: uuid.UUID, user: User, title: str) -> ChatThread:
    async with get_async_db_session() as session:
        thread = await _get_owned_thread(session, thread_id, user)
        thread.title = title
        session.add(thread)
        await session.commit()
        await session.refresh(thread)
        return thread


async def set_archived(
    thread_id: uuid.UUID, user: User, is_archived: bool
) -> ChatThread:
    async with get_async_db_session() as session:
        thread = await _get_owned_thread(session, thread_id, user)
        thread.is_archived = is_archived
        session.add(thread)
        await session.commit()
        await session.refresh(thread)
        return thread


async def delete_thread(thread_id: uuid.UUID, user: User) -> None:
    async with get_async_db_session() as session:
        thread = await _get_owned_thread(session, thread_id, user)
        await session.delete(thread)  # cascades to messages
        await session.commit()


async def list_messages(thread_id: uuid.UUID, user: User) -> Sequence[ChatMessage]:
    async with get_async_db_session() as session:
        await _get_owned_thread(session, thread_id, user)  # ownership check
        stmt = (
            select(ChatMessage)
            .where(col(ChatMessage.thread_id) == thread_id)
            .order_by(col(ChatMessage.created_at).asc())
        )
        return list((await session.execute(stmt)).scalars().all())


async def append_message(
    thread_id: uuid.UUID,
    user: User,
    message_id: str,
    parent_id: Optional[str],
    content: dict[str, Any],
) -> ChatMessage:
    """Insert a message, or update it in place if the id already exists."""
    async with get_async_db_session() as session:
        thread = await _get_owned_thread(session, thread_id, user)

        stmt = select(ChatMessage).where(
            col(ChatMessage.thread_id) == thread_id,
            col(ChatMessage.message_id) == message_id,
        )
        message = (await session.execute(stmt)).scalar_one_or_none()

        if message is None:
            message = ChatMessage(
                thread_id=thread_id,
                message_id=message_id,
                parent_id=parent_id,
                content=content,
            )
            session.add(message)
        else:
            message.parent_id = parent_id
            message.content = content
            session.add(message)

        thread.last_updated_at = datetime.utcnow()
        session.add(thread)

        await session.commit()
        await session.refresh(message)
        return message
