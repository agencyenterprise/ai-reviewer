import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from sqlmodel import SQLModel, Field, Relationship


class Chat(SQLModel, table=True):
    __tablename__ = "chats"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    agent_id: str = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    )
    workflow_id: str = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=True)
    )  # Nullable
    user_id: str = Field(sa_column=Column(String(255), nullable=False))  # User ID
    history: dict = Field(
        sa_column=Column(JSON, nullable=False)
    )  # Serialized session state
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), default=datetime.utcnow, nullable=False
        )
    )
    last_updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )
    )

    # Relationships
    # agent = Relationship(back_populates="chats")
    # workflow = Relationship(back_populates="chats")

    def __repr__(self):
        return (
            f"<Chat(id={self.id}, agent_id={self.agent_id}, user_id='{self.user_id}')>"
        )
