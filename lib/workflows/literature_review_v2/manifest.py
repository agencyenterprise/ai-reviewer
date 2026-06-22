from langgraph.graph import START, StateGraph
from langgraph.graph.state import END

from lib.workflows.context import ContextSchema
from lib.workflows.literature_review_v2.nodes.literature_review import literature_review
from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest
from lib.workflows.simple_deep_agent.state import SimpleDeepAgentState


class LiteratureReviewV2Manifest(SimpleDeepAgentManifest):
    """Literature review implemented with the simple deep-agent pattern.

    Same goal as v1 (surface relevant academic sources the document may have
    missed, both supporting and conflicting), but returns the standard
    simple-deep-agent output (`AgentCheckResult`: issues + report_markdown).

    Reuses ``SimpleDeepAgentState``/``SimpleDeepAgentConfig`` and the base
    ``create_initial_state`` / ``convert_state_to_issues``; only the graph is
    customised so the agent can use web search and receive the document's
    extracted bibliography + publication date in its prompt.
    """

    type = WorkflowRunType.LITERATURE_REVIEW_V2
    name = "Literature Review"
    description = "Are there relevant sources you may have missed? Searches the web for academic sources related to your document's claims, surfacing both supporting and conflicting papers that have not already been cited."
    needs_web_search = True
    is_experimental = True
    required_dependencies = [
        WorkflowRunType.REFERENCE_EXTRACTION,
    ]

    def build_graph(self) -> StateGraph:
        graph = StateGraph(SimpleDeepAgentState, context_schema=ContextSchema)

        graph.add_node("literature_review", literature_review)
        graph.add_edge(START, "literature_review")
        graph.add_edge("literature_review", END)

        return graph  # type: ignore[return-value]
