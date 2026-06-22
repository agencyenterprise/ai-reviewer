from langgraph.graph import START, StateGraph
from langgraph.graph.state import END

from lib.workflows.context import ContextSchema
from lib.workflows.live_reports_v2.nodes.live_reports import live_reports
from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest
from lib.workflows.simple_deep_agent.state import SimpleDeepAgentState


class LiveReportsV2Manifest(SimpleDeepAgentManifest):
    """Live Reports implemented with the simple deep-agent pattern.

    Same goal as v1 (surface newer sources published after the document's
    publication date that update or challenge its claims, and produce an
    addendum), but returns the standard simple-deep-agent output
    (`AgentCheckResult`: issues + report_markdown).

    Reuses ``SimpleDeepAgentState``/``SimpleDeepAgentConfig`` and the base
    ``create_initial_state`` / ``convert_state_to_issues``; only the graph is
    customised so the agent can use web search and receive the document's
    extracted bibliography + publication date in its prompt.
    """

    type = WorkflowRunType.LIVE_REPORTS_V2
    name = "Live Reports"
    description = "Have any of your findings been updated or contradicted by newer research? Searches the web for sources published after your document's publish date that may update or challenge your claims. Generates an addendum containing any new evidence."
    needs_web_search = True
    is_experimental = True
    required_dependencies = [
        WorkflowRunType.REFERENCE_EXTRACTION,
    ]

    def build_graph(self) -> StateGraph:
        graph = StateGraph(SimpleDeepAgentState, context_schema=ContextSchema)

        graph.add_node("live_reports", live_reports)
        graph.add_edge(START, "live_reports")
        graph.add_edge("live_reports", END)

        return graph  # type: ignore[return-value]
