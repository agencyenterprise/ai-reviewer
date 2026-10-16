"""Shared state and config for simple deep-agent workflows.

All single-node deep-agent workflows share these concrete classes.
The `type` field carries a plain WorkflowRunType (no Literal discriminator)
because deserialization always goes through the manifest's get_state_type(),
not Pydantic union dispatch.
"""

from pydantic import Field

from lib.workflows.agent_messages import AgentMessages
from lib.workflows.models import BaseWorkflowConfig, BaseWorkflowState, WorkflowRunType
from lib.workflows.simple_deep_agent.agent_types import DeepAgentResult


class SimpleDeepAgentConfig(BaseWorkflowConfig):
    """Shared config for all simple deep-agent workflows."""

    type: WorkflowRunType = Field(
        description="The workflow type, set per-manifest at runtime"
    )


class SimpleDeepAgentState(BaseWorkflowState):
    """Shared state for all single-node deep-agent workflows.

    ``result`` is the DeepAgentResult, filled from the report file and the
    issues the agent reported through its tool.
    """

    type: WorkflowRunType = Field(
        description="The workflow type, set per-manifest at runtime"
    )
    config: SimpleDeepAgentConfig
    result: DeepAgentResult | None = Field(
        default=None,
        description="Result from the deep agent pass (markdown report and issues)",
    )
    messages: AgentMessages = Field(
        default_factory=list,
        description="LLM conversation messages from the agent invocation.",
    )
