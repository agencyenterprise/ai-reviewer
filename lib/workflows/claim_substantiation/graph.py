from langgraph.graph import StateGraph

from lib.workflows.claim_substantiation.nodes.prepare_documents import prepare_documents
from lib.workflows.claim_substantiation.nodes.check_claim_common_knowledge import (
    check_claim_common_knowledge,
)
from lib.workflows.claim_substantiation.nodes.detect_citations import detect_citations
from lib.workflows.claim_substantiation.nodes.detect_claims import detect_claims
from lib.workflows.claim_substantiation.nodes.detect_claims_toulmin import (
    detect_claims_toulmin,
)
from lib.workflows.claim_substantiation.nodes.extract_references import (
    extract_references,
)
from lib.workflows.claim_substantiation.nodes.review_literature import (
    literature_review,
)
from lib.workflows.claim_substantiation.nodes.suggest_citations import (
    suggest_citations,
)
from lib.workflows.claim_substantiation.nodes.split_into_chunks import split_into_chunks
from lib.workflows.claim_substantiation.nodes.substantiate_claims import (
    substantiate_claims,
)
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState


def build_claim_substantiator_graph(
    use_toulmin: bool = False,
    run_literature_review: bool = True,
    run_suggest_citations: bool = True,
):
    graph = StateGraph(ClaimSubstantiatorState)

    graph.add_node("prepare_documents", prepare_documents)
    if run_literature_review:
        graph.add_node("literature_review", literature_review)
    if run_suggest_citations:
        graph.add_node("suggest_citations", suggest_citations)
    graph.add_node("split_into_chunks", split_into_chunks)
    graph.add_node(
        "detect_claims", detect_claims if not use_toulmin else detect_claims_toulmin
    )
    graph.add_node("detect_citations", detect_citations)
    graph.add_node("extract_references", extract_references)
    graph.add_node("check_claim_common_knowledge", check_claim_common_knowledge)
    graph.add_node("substantiate_claims", substantiate_claims)

    graph.add_node("wait_for_claims_citations", lambda state: {})

    graph.set_entry_point("prepare_documents")

    graph.add_edge("prepare_documents", "split_into_chunks")
    if run_literature_review:
        graph.add_edge("prepare_documents", "literature_review")

    graph.add_edge("split_into_chunks", "extract_references")
    graph.add_edge("split_into_chunks", "detect_claims")

    graph.add_edge("extract_references", "detect_citations")

    # # Both detect_claims and detect_citations must complete before wait_for_claims_citations
    graph.add_edge("detect_claims", "wait_for_claims_citations")
    graph.add_edge("detect_citations", "wait_for_claims_citations")

    # Only after detect_claims, detect_citations, and check_claim_common_knowledge are complete, proceed to substantiate_claims
    graph.add_edge("wait_for_claims_citations", "check_claim_common_knowledge")
    graph.add_edge("check_claim_common_knowledge", "substantiate_claims")

    # Suggest citations (aim 2.a)
    # Must wait for ALL processing to complete before suggesting citations
    if run_suggest_citations:
        graph.add_edge("substantiate_claims", "suggest_citations")
        if run_literature_review:
            graph.add_edge("literature_review", "suggest_citations")

        graph.set_finish_point("suggest_citations")
    else:
        graph.set_finish_point("substantiate_claims")

    return graph


if __name__ == "__main__":
    # Print the graph in mermaid format
    # Paste it into https://mermaid.live/ to see the graph

    workflow_graph = build_claim_substantiator_graph()
    app = workflow_graph.compile()
    print(app.get_graph().draw_mermaid())
