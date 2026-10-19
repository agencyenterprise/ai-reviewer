"""A conversation with Draft Detective, on any surface: the shared row.

Every conversation, whether on the web app's /chat page, in the Word add-in's chat or
with the Teams bot, has one row here. It is what other tables point at when something
belongs to a conversation rather than a project, such as the images of a document read
in it (``files.conversation_id``), so they need one foreign key whatever the surface,
and go when the conversation does.

What a surface knows about its conversations stays in its own table, one-to-one by id
(``chat_threads``, ``microsoft_word_chat_threads``, ``microsoft_teams_conversations``):
who owns it, its title, its document. Those differ too much to share columns: a web
thread belongs to a user, a Word chat to a Microsoft account, a Teams conversation to
everyone in it. Deleting the row here deletes the surface's row with it.

``user_id`` connects a conversation to a Draft Detective user, whatever the surface, so
that everything a person said to Draft Detective can be found from their account.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel


class ConversationKind(str, Enum):
    WEB = "web"
    WORD = "word"
    TEAMS = "teams"


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        description="Also the id of the surface's own row for it",
    )
    kind: ConversationKind = Field(
        sa_column=Column(String, nullable=False, index=True),
        description="Which surface it is on, so which table holds the rest",
    )
    user_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True),
            # Listing only, so deleting the user unlists the conversation rather than
            # deleting it: a Teams conversation belongs to everyone in it.
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        description=(
            "The Draft Detective user it is listed under: the web thread's owner, or the "
            "user whose email a Microsoft account signs in with "
            "(``lib/services/microsoft/linked_users.py``). For listing only: each "
            "surface checks access by its own owner, never by this."
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
