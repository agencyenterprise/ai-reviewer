import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..config.database import Base


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    stages = Column(
        JSON, nullable=False
    )  # Array of Arrays of agent_ids (copied from workflow)
    chat_ids = Column(JSON)  # Array of arrays of chat_id's associated with each agent
    chat_results = Column(JSON)  # Serialized representation of chat results
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship to workflow
    workflow = relationship("Workflow", back_populates="workflow_runs")

    def __repr__(self):
        return f"<WorkflowRun(id={self.id}, workflow_id={self.workflow_id})>"
