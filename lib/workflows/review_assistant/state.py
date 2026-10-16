"""State and config for the Review Assistant workflow.

One run is one request: the outputs the author asked for and the documents they
handed over, unlabeled. The agent works out what each document is, and the run
keeps one HTML report per requested output.
"""

from enum import Enum
from typing import Literal

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field, field_serializer

from lib.workflows.models import BaseWorkflowConfig, BaseWorkflowState, WorkflowRunType


class ReviewAssistantOutput(str, Enum):
    """The deliverables the review-assistant skill can produce."""

    REVISION_PLANNING_SUMMARY = "revision_planning_summary"
    REVIEWER_RESPONSE_MEMOS = "reviewer_response_memos"
    REVIEWER_COVERAGE_REPORT = "reviewer_coverage_report"


class ReviewAssistantConfig(BaseWorkflowConfig):
    type: Literal[WorkflowRunType.REVIEW_ASSISTANT] = WorkflowRunType.REVIEW_ASSISTANT
    outputs: list[ReviewAssistantOutput] = Field(
        default_factory=list, description="The deliverables to produce, at least one"
    )
    input_file_ids: list[str] = Field(
        default_factory=list,
        description="Every document to read, in the order the author gave them",
    )


class ReviewAssistantInput(BaseModel):
    """One document as it was mounted for the agent."""

    file_id: str
    file_name: str
    folder: str = Field(
        description="Its folder on the agent filesystem, e.g. /inputs/01-memo"
    )
    comment_count: int = 0
    tracked_change_count: int = 0


class ReviewAssistantInputReading(BaseModel):
    """What the agent decided a document is. Read from the agent's own notes,
    so every field but the folder is optional."""

    folder: str
    role: str = ""
    reviewer: str | None = None
    note: str | None = None


class ReviewAssistantReport(BaseModel):
    output: ReviewAssistantOutput
    report_html: str


class ReviewAssistantState(BaseWorkflowState):
    type: Literal[WorkflowRunType.REVIEW_ASSISTANT] = WorkflowRunType.REVIEW_ASSISTANT
    config: ReviewAssistantConfig
    inputs: list[ReviewAssistantInput] = Field(default_factory=list)
    input_readings: list[ReviewAssistantInputReading] = Field(default_factory=list)
    reports: list[ReviewAssistantReport] = Field(default_factory=list)
    guard_message: str | None = Field(
        default=None,
        description="Why the run stopped before the agent started, when it did",
    )
    messages: list[BaseMessage] = Field(default_factory=list)

    @field_serializer("messages")
    @classmethod
    def _serialize_messages(cls, messages: list[BaseMessage]) -> list[dict]:
        # Checkpointer-hydrated states may contain raw dicts in `messages`.
        return [m if isinstance(m, dict) else m.model_dump() for m in messages]
