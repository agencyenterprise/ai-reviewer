from typing import Literal

from pydantic import Field

from lib.workflows.agent_messages import AgentMessages
from lib.workflows.models import BaseWorkflowConfig, BaseWorkflowState, WorkflowRunType


class Reviewer2Config(BaseWorkflowConfig):
    """Configuration for the Reviewer 2 workflow."""

    type: Literal[WorkflowRunType.REVIEWER_2] = Field(WorkflowRunType.REVIEWER_2)


class Reviewer2State(BaseWorkflowState):
    """State for the Reviewer 2 workflow."""

    type: Literal[WorkflowRunType.REVIEWER_2] = Field(WorkflowRunType.REVIEWER_2)
    config: Reviewer2Config
    file_id: str = Field(default="", description="Main document file ID")
    peer_review_markdown: str | None = Field(
        default=None,
        description="The peer review document as markdown (Sections 1-4)",
    )
    rebuttal_markdown: str | None = Field(
        default=None,
        description="The rebuttal document as markdown",
    )
    messages: AgentMessages = Field(
        default_factory=list,
        description="The reviewer agent's full conversation, system prompt included.",
    )
