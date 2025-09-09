import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from ..config.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    model = Column(String(255), nullable=False)  # Format: "{provider}:{model}"
    prompt = Column(Text, nullable=False)
    mandatory_tools = Column(ARRAY(String), default=list)  # Array of tool identifiers
    disallowed_tools = Column(ARRAY(String), default=list)  # Array of tool identifiers
    dependencies = Column(ARRAY(UUID), default=list)  # Array of agent IDs
    output_schema = Column(JSON)  # JSON Schema for expected output
    version = Column(Integer, default=1)
    created_by = Column(String(255), nullable=False)  # User ID
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chats = relationship("Chat", back_populates="agent")

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', version={self.version})>"
