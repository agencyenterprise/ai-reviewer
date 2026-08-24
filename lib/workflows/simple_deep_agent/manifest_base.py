"""Base manifests for single-node deep-agent workflows.

Two variants share one base and one state (``SimpleDeepAgentState`` with a
unified ``DeepAgentResult``):

- ``SimpleDeepAgentManifest`` — the LLM fills ``AgentCheckResult`` (issues + a
  markdown report).
- ``HtmlReportDeepAgentManifest`` — the LLM writes a single self-contained HTML
  document to ``REPORT_PATH`` on the agent filesystem, no structured output and
  no issues.

Either way the node maps what the agent produced into the shared
``DeepAgentResult`` stored in state, and the UI renders whichever report field
is present. That mapping is the point of the split: the two variants deliver
their results by different mechanisms, and state does not know or care.

Subclasses declare class-level attributes (type, name, description, and either
`skill` or `user_prompt`) and the usual WorkflowManifest metadata fields.
"""

import html as html_lib
from typing import TYPE_CHECKING, ClassVar, List, Literal, Optional, Type

from langgraph.graph import START, StateGraph
from langgraph.graph.state import END
from langgraph.runtime import Runtime
from pydantic import BaseModel

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
    REPORT_PATH,
    AgentCheckResult,
    DeepAgentResult,
    DeepAgentRun,
    IssueItem,
    ReportNotWrittenError,
    issues_from_agent_result,
)

if TYPE_CHECKING:
    from lib.services.file_artifacts_service.file_artifacts_service_type import (
        FileArtifactsServiceType,
    )
    from lib.workflows.workflow_types import WorkflowState


class _BaseDeepAgentManifest(
    WorkflowManifest[SimpleDeepAgentState, SimpleDeepAgentConfig]
):
    """Shared machinery for single-node deep-agent workflows.

    Subclasses set ``result_model`` (the LLM's structured-output schema, or
    ``None`` for a variant that does not use structured output),
    implement ``_guard_result`` (how a ``precheck`` message is surfaced), and
    ``convert_state_to_issues``. State, graph, prompt resolution, and the
    LLM-output → ``DeepAgentResult`` mapping are shared.

    The agent's backend always exposes the full project file tree (current main,
    supporting docs, and a /revisions/<n>/ tree with each revision's main and
    reviewer memos); workflows point the agent at the paths they need via the
    system prompt rather than by selecting files here.
    """

    skill: ClassVar[Optional[str]] = None
    user_prompt: ClassVar[Optional[str]] = None
    system_prompt: ClassVar[Optional[str]] = None

    # Structured-output schema the LLM must fill for this variant.
    # None means the variant does not use structured output at all.
    result_model: ClassVar[Optional[Type[BaseModel]]] = AgentCheckResult

    # Per-workflow reasoning effort. None keeps SimpleDeepAgent's default;
    # set it on workflows whose task warrants more deliberation.
    reasoning_effort: ClassVar[Optional[Literal["low", "medium", "high"]]] = None

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

    async def precheck(self, service: "FileArtifactsServiceType") -> Optional[str]:
        """Optional guard run before the agent.

        Return a message to short-circuit: the agent is skipped and the message
        is surfaced as the run's report. Return None to proceed. Default: no guard.
        """
        return None

    def _guard_result(self, message: str) -> DeepAgentResult:
        """Build the state result carrying a precheck guard message."""
        raise NotImplementedError

    def _to_state_result(self, run: DeepAgentRun) -> DeepAgentResult:
        """Map what the agent produced into the unified DeepAgentResult."""
        raise NotImplementedError

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
                return {"result": manifest._guard_result(guard_message), "messages": []}

            agent = SimpleDeepAgent(
                context=runtime.context,
                system_prompt=manifest.system_prompt,
                user_prompt=manifest.resolve_user_prompt(),
                response_model=manifest.result_model,
                reasoning_effort=manifest.reasoning_effort,
            )
            run = await agent.ainvoke({})
            return {
                "result": manifest._to_state_result(run),
                "messages": run.messages,
            }

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
        # Both variants may carry issues in the unified result (the HTML variant
        # can populate them too); convert whatever is present.
        if state.result is None:
            return []
        return issues_from_agent_result(state.result, self.type)


class SimpleDeepAgentManifest(_BaseDeepAgentManifest):
    """Deep-agent workflow whose LLM fills issues plus a markdown report."""

    result_model: ClassVar[Optional[Type[BaseModel]]] = AgentCheckResult

    def _to_state_result(self, run: DeepAgentRun) -> DeepAgentResult:
        output = run.structured_response
        issues = getattr(output, "issues", None) or []
        return DeepAgentResult(
            issues=[i for i in issues if isinstance(i, IssueItem)],
            report_markdown=getattr(output, "report_markdown", "") or "",
        )

    def _guard_result(self, message: str) -> DeepAgentResult:
        return DeepAgentResult(report_markdown=message)


class HtmlReportDeepAgentManifest(_BaseDeepAgentManifest):
    """Deep-agent workflow that writes a self-contained HTML report to a file.

    No structured output: the agent is told to write its deliverable to
    ``REPORT_PATH`` and the node reads it back off the agent filesystem. What
    lands in state is unchanged -- ``DeepAgentResult.report_html``, the same
    field the UI has always rendered -- so this is a change of delivery
    mechanism only, invisible past this method.
    """

    result_model: ClassVar[Optional[Type[BaseModel]]] = None

    def _to_state_result(self, run: DeepAgentRun) -> DeepAgentResult:
        report = run.files.get(REPORT_PATH, "").strip()
        if not report:
            raise ReportNotWrittenError(REPORT_PATH, list(run.files))
        return DeepAgentResult(report_html=report)

    def _guard_result(self, message: str) -> DeepAgentResult:
        safe = html_lib.escape(message)
        return DeepAgentResult(
            report_html=(
                '<!doctype html><html><head><meta charset="utf-8"></head>'
                f"<body><p>{safe}</p></body></html>"
            )
        )
