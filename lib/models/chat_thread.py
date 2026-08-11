import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlmodel import Field, SQLModel


class ChatThread(SQLModel, table=True):
    """A persisted assistant-ui chat thread belonging to a user."""

    __tablename__ = "chat_threads"
    __table_args__ = (Index("ix_chat_threads_user_id", "user_id"),)

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        description="The unique identifier for the chat thread",
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="Owner of the thread",
    )
    title: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="Human-readable thread title (generated from the conversation)",
    )
    is_archived: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
        description="Whether the thread is archived",
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), default=datetime.utcnow, nullable=False
        ),
    )
    last_updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        ),
    )


class ChatMessage(SQLModel, table=True):
    """A single persisted message within a chat thread.

    `content` stores the assistant-ui `ExportedMessageRepositoryItem`
    (`{ message, parentId, runConfig? }`) verbatim so the full message —
    including reasoning and tool-call parts — round-trips on reload.
    """

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_thread_created", "thread_id", "created_at"),
        Index("ix_chat_messages_thread_message", "thread_id", "message_id", unique=True),
    )

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    )
    thread_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("chat_threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    # assistant-ui message id (unique within a thread) used for upserts.
    message_id: str = Field(sa_column=Column(String, nullable=False))
    parent_id: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    content: dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False),
        description="The ExportedMessageRepositoryItem JSON",
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), default=datetime.utcnow, nullable=False
        ),
    )
