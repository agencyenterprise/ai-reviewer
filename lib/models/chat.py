import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..config.database import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    workflow_id = Column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=True
    )  # Nullable
    user_id = Column(String(255), nullable=False)  # User ID
    history = Column(JSON, nullable=False)  # Serialized session state
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    agent = relationship("Agent", back_populates="chats")
    workflow = relationship("Workflow", back_populates="chats")

    def __repr__(self):
        return (
            f"<Chat(id={self.id}, agent_id={self.agent_id}, user_id='{self.user_id}')>"
        )
