import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from sqlmodel import SQLModel, Field, Relationship


class Workflow(SQLModel, table=True):
    __tablename__ = "workflows"

    id: str = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(sa_column=Column(Text))
    stages: list[list[str]] = Field(
        sa_column=Column(JSON, nullable=False)
    )  # Array of Arrays of agent_ids
    created_by: str = Field(sa_column=Column(String(255), nullable=False))  # User ID
    created_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))

    # Relationships
    # workflow_runs = Relationship(back_populates="workflow")
    # chats = Relationship(back_populates="workflow")

    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}')>"
