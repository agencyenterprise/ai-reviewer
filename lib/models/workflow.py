import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..config.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    stages = Column(JSON, nullable=False)  # Array of Arrays of agent_ids
    created_by = Column(String(255), nullable=False)  # User ID
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow_runs = relationship("WorkflowRun", back_populates="workflow")
    chats = relationship("Chat", back_populates="workflow")

    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}')>"
