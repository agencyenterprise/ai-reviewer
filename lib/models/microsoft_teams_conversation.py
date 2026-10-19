"""A conversation with the Draft Detective bot in Teams.

Its row in ``conversations`` is what the documents' images opened in it belong to. The
conversation itself is in the LangGraph checkpointer, keyed by the Teams conversation id
as Teams sends it, so a follow-up in Teams is a follow-up for the agent: in a channel
that id carries a ``;messageid=`` suffix per reply chain, making each chain its own
conversation. It belongs to no one person: everyone in the chat or reply chain shares it.
"""

import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel


class MicrosoftTeamsConversation(SQLModel, table=True):
    __tablename__ = "microsoft_teams_conversations"

    id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("conversations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        description="The conversation's id in ``conversations``",
    )
    teams_conversation_id: str = Field(
        sa_column=Column(String, nullable=False, unique=True),
        description="The id Teams gives the conversation; also its LangGraph thread id",
    )
