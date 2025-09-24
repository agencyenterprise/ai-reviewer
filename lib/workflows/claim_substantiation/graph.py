from langgraph.graph import StateGraph

from lib.config.langfuse import langfuse_handler
from lib.workflows.claim_substantiation.nodes.detect_citations import detect_citations
from lib.workflows.claim_substantiation.nodes.detect_claims import detect_claims
from lib.workflows.claim_substantiation.nodes.detect_claims_toulmin import (
    detect_claims_toulmin,
)
from lib.workflows.claim_substantiation.nodes.extract_references import (
    extract_references,
)
from lib.workflows.claim_substantiation.nodes.split_into_chunks import split_into_chunks
from lib.workflows.claim_substantiation.nodes.substantiate_claims import (
    substantiate_claims,
)
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState


def build_claim_substantiator_graph(use_toulmin: bool = False, session_id: str = None):
    graph = StateGraph(ClaimSubstantiatorState)

    graph.add_node("split_into_chunks", split_into_chunks)
    graph.add_node(
        "detect_claims", detect_claims if not use_toulmin else detect_claims_toulmin
    )
    graph.add_node("detect_citations", detect_citations)
    graph.add_node("extract_references", extract_references)
    graph.add_node("substantiate_claims", substantiate_claims, defer=True)

    graph.set_entry_point("split_into_chunks")
    graph.add_edge("split_into_chunks", "extract_references")
    graph.add_edge("split_into_chunks", "detect_claims")

    graph.add_edge("extract_references", "detect_citations")

    # substantiate claims when both claims and citations are present
    graph.add_edge("detect_citations", "substantiate_claims")
    graph.add_edge("detect_claims", "substantiate_claims")

    graph.set_finish_point("substantiate_claims")

    return graph.compile().with_config({"callbacks": [langfuse_handler], "metadata": {"langfuse_session_id": session_id}})


if __name__ == "__main__":
    # Print the graph in mermaid format
    # Paste it into https://mermaid.live/ to see the graph

    app = build_claim_substantiator_graph()
    print(app.get_graph().draw_mermaid())
