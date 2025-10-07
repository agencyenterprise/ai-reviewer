from langgraph.graph import StateGraph

from lib.workflows.claim_substantiation.nodes.check_claim_common_knowledge import (
    check_claim_common_knowledge,
)
from lib.workflows.claim_substantiation.nodes.detect_citations import detect_citations
from lib.workflows.claim_substantiation.nodes.extract_claims import extract_claims
from lib.workflows.claim_substantiation.nodes.extract_claims_toulmin import (
    extract_claims_toulmin,
)
from lib.workflows.claim_substantiation.nodes.extract_references import (
    extract_references,
)
from lib.workflows.claim_substantiation.nodes.prepare_documents import prepare_documents
from lib.workflows.claim_substantiation.nodes.review_literature import literature_review
from lib.workflows.claim_substantiation.nodes.split_into_chunks import split_into_chunks
from lib.workflows.claim_substantiation.nodes.suggest_citations import suggest_citations
from lib.workflows.claim_substantiation.nodes.summarize_supporting_documents import (
    summarize_supporting_documents,
)
from lib.workflows.claim_substantiation.nodes.verify_claims import verify_claims
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
        graph.add_node("summarize_supporting_documents", summarize_supporting_documents)
        graph.add_node("suggest_citations", suggest_citations, defer=True)
    graph.add_node("split_into_chunks", split_into_chunks)
    graph.add_node(
        "extract_claims", extract_claims if not use_toulmin else extract_claims_toulmin
    )
    graph.add_node("detect_citations", detect_citations)
    graph.add_node("extract_references", extract_references)
    graph.add_node("check_claim_common_knowledge", check_claim_common_knowledge)
    graph.add_node("verify_claims", verify_claims, defer=True)

    graph.set_entry_point("prepare_documents")

    graph.add_edge("prepare_documents", "split_into_chunks")
    if run_literature_review:
        graph.add_edge("prepare_documents", "literature_review")
    if run_suggest_citations:
        graph.add_edge("prepare_documents", "summarize_supporting_documents")

    graph.add_edge("split_into_chunks", "extract_references")
    graph.add_edge("split_into_chunks", "extract_claims")
    graph.add_edge("extract_references", "detect_citations")
    graph.add_edge("extract_claims", "check_claim_common_knowledge")
    graph.add_edge("check_claim_common_knowledge", "verify_claims")
    graph.add_edge("detect_citations", "verify_claims")

    # Suggest citations (aim 2.a)
    # Must wait for ALL processing to complete before suggesting citations
    if run_suggest_citations:
        graph.add_edge("verify_claims", "suggest_citations")
        graph.add_edge("summarize_supporting_documents", "suggest_citations")
        if run_literature_review:
            graph.add_edge("literature_review", "suggest_citations")

        graph.set_finish_point("suggest_citations")
    else:
        graph.set_finish_point("verify_claims")

    return graph


if __name__ == "__main__":
    # Print the graph in mermaid format
    # Paste it into https://mermaid.live/ to see the graph

    workflow_graph = build_claim_substantiator_graph(
        run_literature_review=False, run_suggest_citations=False
    )
    app = workflow_graph.compile()
    print(app.get_graph().draw_mermaid())
