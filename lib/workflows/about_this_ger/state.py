"""State definitions for About This (GER) workflow."""

from operator import add
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from lib.workflows.agent_messages import AgentMessages
from lib.workflows.models import BaseWorkflowConfig, BaseWorkflowState, WorkflowRunType
from lib.workflows.simple_deep_agent.agent_types import AgentCheckResult, IssueItem

__all__ = [
    "AgentCheckResult",
    "AgentConversation",
    "IssueItem",
    "AboutThisGerConfig",
    "AboutThisGerState",
]


class AgentConversation(BaseModel):
    """One validator agent's full conversation, system prompt included."""

    name: str = Field(description='Which validator ran it: "preface" or "authors".')
    messages: AgentMessages = Field(default_factory=list)


class AboutThisGerConfig(BaseWorkflowConfig):
    """Configuration for the About This (GER) workflow."""

    type: Literal[WorkflowRunType.ABOUT_THIS_GER] = Field(
        WorkflowRunType.ABOUT_THIS_GER
    )


class AboutThisGerState(BaseWorkflowState):
    """State for the About This (GER) workflow."""

    type: Literal[WorkflowRunType.ABOUT_THIS_GER] = Field(
        WorkflowRunType.ABOUT_THIS_GER
    )
    config: AboutThisGerConfig

    preface_result: AgentCheckResult | None = Field(
        default=None,
        description="Result from the preface validation deep agent",
    )
    authors_result: AgentCheckResult | None = Field(
        default=None,
        description="Result from the authors validation deep agent",
    )
    # The two validators run in parallel, so each appends its own conversation.
    agent_conversations: Annotated[list[AgentConversation], add] = Field(
        default_factory=list,
        description="Each validator agent's conversation, for debugging and eval transcripts.",
    )
