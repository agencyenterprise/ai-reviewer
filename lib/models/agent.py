import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlmodel import JSON, Field, Relationship, SQLModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from pydantic import BaseModel


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: str = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(sa_column=Column(Text))
    model: str = Field(
        sa_column=Column(String(255), nullable=False)
    )  # Format: "{provider}:{model}"
    prompt: str = Field(sa_column=Column(Text, nullable=False))
    mandatory_tools: list[str] = Field(
        sa_column=Column(ARRAY(String), default=list)
    )  # Array of tool identifiers
    disallowed_tools: list[str] = Field(
        sa_column=Column(ARRAY(String), default=list)
    )  # Array of tool identifiers
    dependencies: list[str] = Field(
        sa_column=Column(ARRAY(UUID), default=list)
    )  # Array of agent IDs
    output_schema: dict = Field(
        sa_column=Column(JSON)
    )  # JSON Schema for expected output
    version: int = Field(sa_column=Column(Integer, default=1))
    created_by: str = Field(sa_column=Column(String(255), nullable=False))  # User ID
    created_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))

    # Relationships
    # chats = Relationship(back_populates="agent")

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', version={self.version})>"

    @property
    def model_provider(self):
        return self.model.split(":")[0]

    @property
    def model_name(self):
        return self.model.split(":")[1]

    def prep_llm_args(self, prompt_kwargs: dict):
        llm = init_chat_model(self.model_name, model_provider=self.model_provider)
        llm_with_structure = llm.with_structured_output(self.output_schema)

        # Create prompt
        messages = self.prompt.format_messages(**prompt_kwargs)

        # Apply LLM
        args = {
            "input": messages,
            "config": {"callbacks": [langfuse_handler]},
        }
        return llm_with_structure, args

    async def apply(self, prompt_kwargs: dict):
        llm_with_structure, args = self.prep_llm_args(prompt_kwargs)
        chunk_result = await llm_with_structure.ainvoke(
            args["input"],
            config=args["config"],
        )
        return chunk_result

    def apply_sync(self, prompt_kwargs: dict):
        llm_with_structure, args = self.prep_llm_args(prompt_kwargs)
        chunk_result = llm_with_structure.invoke(
            args["input"],
            config=args["config"],
        )
        return chunk_result
