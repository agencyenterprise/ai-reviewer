"""State definitions for reference extraction workflow."""

from typing import Literal

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field, field_serializer

from lib.workflows.models import BaseWorkflowConfig, BaseWorkflowState, WorkflowRunType


class ExtractedReference(BaseModel):
    """A reference extracted from the document."""

    id: str = Field(description="Unique identifier for this reference")
    text: str = Field(description="The extracted reference text")
    start_line: int | None = Field(
        default=None, description="1-indexed starting line number in the markdown"
    )
    end_line: int | None = Field(
        default=None, description="1-indexed ending line number in the markdown"
    )


class ReferenceExtractionConfig(BaseWorkflowConfig):
    """Configuration for reference extraction workflow."""

    type: Literal[WorkflowRunType.REFERENCE_EXTRACTION] = Field(
        default=WorkflowRunType.REFERENCE_EXTRACTION
    )


class ReferenceExtractionState(BaseWorkflowState):
    """State for reference extraction workflow."""

    type: Literal[WorkflowRunType.REFERENCE_EXTRACTION] = Field(
        default=WorkflowRunType.REFERENCE_EXTRACTION
    )

    # Inputs
    config: ReferenceExtractionConfig
    file_id: str = Field(description="ID of the main document")

    # Outputs
    extracted_references: list[ExtractedReference] = Field(
        default_factory=list, description="Extracted references with unique IDs"
    )
    reasoning: str = Field(
        default="",
        description="Step-by-step reasoning describing how references were found and extracted",
    )
    messages: list[BaseMessage] = Field(
        default_factory=list,
        description="LLM conversation messages from the agent invocation.",
    )

    @field_serializer("messages")
    @classmethod
    def _serialize_messages(cls, messages: list[BaseMessage]) -> list[dict]:
        # Checkpointer-hydrated states may contain raw dicts in `messages`
        # because reducers can append items that bypass model construction.
        return [m if isinstance(m, dict) else m.model_dump() for m in messages]
