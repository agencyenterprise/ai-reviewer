"""Base manifest for simple single-node deep-agent workflows.

Subclasses only need to declare class-level attributes (type, name, description,
and either `skill` or `user_prompt`) and the usual WorkflowManifest metadata
fields. The graph, node, state construction, and issue conversion are all
handled here.
"""

from typing import TYPE_CHECKING, ClassVar, List, Optional, Type

from langgraph.graph import START, StateGraph
from langgraph.graph.state import END
from langgraph.runtime import Runtime

from lib.workflows.context import ContextSchema
from lib.workflows.decorators import register_node
from lib.workflows.manifest import WorkflowManifest
from lib.workflows.models import DocumentIssue
from lib.workflows.simple_deep_agent.agent import SimpleDeepAgent
from lib.skills import load_skill_prompt
from lib.workflows.simple_deep_agent.state import (
    SimpleDeepAgentConfig,
    SimpleDeepAgentState,
)
from lib.workflows.simple_deep_agent.agent_types import (
    AgentCheckResult,
    issues_from_agent_result,
)

if TYPE_CHECKING:
    from lib.services.file_artifacts_service.file_artifacts_service_type import (
        FileArtifactsServiceType,
    )
    from lib.workflows.workflow_types import WorkflowState


class SimpleDeepAgentManifest(
    WorkflowManifest[SimpleDeepAgentState, SimpleDeepAgentConfig]
):
    """Base manifest for workflows with a single deep-agent node.

    Subclasses must define:
        type: WorkflowRunType
        name: str
        description: str
        and exactly one prompt source:
            skill: str         — name of the skill under `skills/` whose
                                 SKILL.md body holds the rules/criteria
                                 (the single source of truth, preferred), OR
            user_prompt: str   — the rules/criteria inline (used as the human
                                 message)

    Optional overrides:
        system_prompt: str  — overrides the default generic system prompt
        (plus any WorkflowManifest fields: required_dependencies, order, etc.)

    The agent's backend always exposes the full project file tree (current main,
    supporting docs, and a /revisions/<n>/ tree with each revision's main and
    reviewer memos); workflows point the agent at the paths they need via the
    system prompt rather than by selecting files here.
    """

    skill: ClassVar[Optional[str]] = None
    user_prompt: ClassVar[Optional[str]] = None
    system_prompt: ClassVar[Optional[str]] = None

    def resolve_user_prompt(self) -> str:
        """Resolve the rules/criteria used as the deep agent's user prompt.

        Prefers the referenced skill (the single source of truth) and falls
        back to an inline `user_prompt`. Exactly one must be defined.
        """
        if self.skill is not None:
            return load_skill_prompt(self.skill)
        if self.user_prompt is not None:
            return self.user_prompt
        raise ValueError(
            f"{type(self).__name__} must define either `skill` or `user_prompt`"
        )

    async def precheck(
        self, service: "FileArtifactsServiceType"
    ) -> Optional[str]:
        """Optional guard run before the agent.

        Return a message to short-circuit: the agent is skipped and the message
        is surfaced as the run's ``report_markdown``. Return None to proceed.
        Default: no guard.
        """
        return None

    def get_state_type(self) -> Type[SimpleDeepAgentState]:
        return SimpleDeepAgentState

    def get_config_type(self) -> Type[SimpleDeepAgentConfig]:
        return SimpleDeepAgentConfig

    def build_graph(self) -> StateGraph:
        manifest = self

        async def run_agent(
            state: SimpleDeepAgentState, runtime: Runtime[ContextSchema]
        ) -> dict:
            service = runtime.context.file_artifacts_service

            guard_message = await manifest.precheck(service)
            if guard_message is not None:
                return {
                    "result": AgentCheckResult(
                        issues=[], report_markdown=guard_message
                    ),
                    "messages": [],
                }

            agent = SimpleDeepAgent(
                context=runtime.context,
                system_prompt=manifest.system_prompt,
                user_prompt=manifest.resolve_user_prompt(),
            )
            result, messages = await agent.ainvoke({})
            return {"result": result, "messages": messages}

        decorated = register_node(self.name)(run_agent)

        graph = StateGraph(SimpleDeepAgentState, context_schema=ContextSchema)
        graph.add_node("run_agent", decorated)
        graph.add_edge(START, "run_agent")
        graph.add_edge("run_agent", END)
        return graph  # type: ignore[return-value]

    async def create_initial_state(
        self,
        config: SimpleDeepAgentConfig,
        existing_states: List["WorkflowState"],
        revision: int,
        prior_self_state: SimpleDeepAgentState | None = None,
    ) -> SimpleDeepAgentState:
        return SimpleDeepAgentState(type=self.type, config=config)

    def convert_state_to_issues(
        self,
        state: SimpleDeepAgentState,
        other_states: List["WorkflowState"],
    ) -> List[DocumentIssue]:
        if state.result is None:
            return []
        return issues_from_agent_result(state.result, self.type)
