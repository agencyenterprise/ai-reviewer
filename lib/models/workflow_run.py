import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class WorkflowRun(SQLModel, table=True):
    __tablename__ = "workflow_runs"

    id: str = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    workflow_id: str = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    )
    stages: list[list[str]] = Field(
        sa_column=Column(JSON, nullable=False)
    )  # Array of Arrays of agent_ids (copied from workflow)
    chat_ids: Optional[list[str]] = Field(
        sa_column=Column(JSON, nullable=True)
    )  # Array of chat_ids
    chat_results: dict = Field(
        sa_column=Column(JSON)
    )  # Serialized representation of chat results
    created_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))
    last_updated_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Relationship to workflow
    # workflow = Relationship(back_populates="workflow_runs")

    def __repr__(self):
        return f"<WorkflowRun(id={self.id}, workflow_id={self.workflow_id})>"
