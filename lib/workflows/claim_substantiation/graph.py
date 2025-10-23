from langgraph.graph import StateGraph

from lib.workflows.claim_substantiation.nodes.check_claim_needs_substantiation import (
    check_claim_needs_substantiation,
)
from lib.workflows.claim_substantiation.nodes.detect_citations import detect_citations
from lib.workflows.claim_substantiation.nodes.extract_claims import extract_claims
from lib.workflows.claim_substantiation.nodes.extract_claims_toulmin import (
    extract_claims_toulmin,
)
from lib.workflows.claim_substantiation.nodes.extract_references import (
    extract_references,
)
from lib.workflows.claim_substantiation.nodes.index_supporting_documents import (
    index_supporting_documents,
)
from lib.workflows.claim_substantiation.nodes.prepare_documents import prepare_documents
from lib.workflows.claim_substantiation.nodes.review_literature import literature_review
from lib.workflows.claim_substantiation.nodes.split_into_chunks import split_into_chunks
from lib.workflows.claim_substantiation.nodes.suggest_citations import suggest_citations
from lib.workflows.claim_substantiation.nodes.summarize_supporting_documents import (
    summarize_supporting_documents,
)
from lib.workflows.claim_substantiation.nodes.verify_claims import (
    verify_claims,
    verify_claims_with_rag,
)
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.workflows.claim_substantiation.nodes.generate_live_reports import (
    generate_live_reports_analysis,
)
from lib.workflows.claim_substantiation.nodes.categorize_claims import categorize_claims


def finalize(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    return {}


def build_claim_substantiator_graph(
    use_toulmin: bool = False,
    run_literature_review: bool = True,
    run_suggest_citations: bool = True,
    use_rag: bool = True,
    run_live_reports: bool = False,
) -> StateGraph:
    """
    Build a LangGraph workflow for claim substantiation analysis.

    Args:
        use_toulmin: Use Toulmin model for claim extraction
        run_literature_review: Include literature review node
        run_suggest_citations: Include citation suggestion nodes
        use_rag: Use RAG-based claim verification

    Returns:
        Configured StateGraph for claim substantiation workflow
    """

    graph = StateGraph(ClaimSubstantiatorState)

    # Core nodes
    graph.add_node("prepare_documents", prepare_documents)
    graph.add_node("split_into_chunks", split_into_chunks)
    graph.add_node(
        "extract_claims", extract_claims if not use_toulmin else extract_claims_toulmin
    )
    graph.add_node("detect_citations", detect_citations)
    graph.add_node("extract_references", extract_references)
    graph.add_node("check_claim_needs_substantiation", check_claim_needs_substantiation)
    graph.add_node("categorize_claims", categorize_claims)

    # Conditional verify node based on RAG setting
    if use_rag:
        graph.add_node("index_supporting_documents", index_supporting_documents)
        verify_node = verify_claims_with_rag
    else:
        verify_node = verify_claims
    graph.add_node("verify_claims", verify_node, defer=True)

    # Optional nodes
    if run_literature_review:
        graph.add_node("literature_review", literature_review)
    if run_suggest_citations:
        graph.add_node("summarize_supporting_documents", summarize_supporting_documents)
        graph.add_node("suggest_citations", suggest_citations, defer=True)
    if run_live_reports:
        graph.add_node(
            "generate_live_reports_analysis", generate_live_reports_analysis, defer=True
        )

    # Finalize/join node to allow parallel branches to complete
    if run_suggest_citations and run_live_reports:
        graph.add_node("finalize", finalize)

    # Entry point
    graph.set_entry_point("prepare_documents")

    # Core edges - main processing pipeline
    graph.add_edge("prepare_documents", "split_into_chunks")
    graph.add_edge("split_into_chunks", "extract_references")
    graph.add_edge("split_into_chunks", "extract_claims")
    graph.add_edge("extract_references", "detect_citations")
    # NOTE (2025-10-21): Currently going directly from extract_claims to check_claim_needs_substantiation
    # and then to verify claims;
    # Later we can likely remove the `check_claim_needs_substantiation` node and just go from  categorize_claims to verify_claims and a future verify_inferences
    graph.add_edge("extract_claims", "categorize_claims")
    graph.add_edge("categorize_claims", "check_claim_needs_substantiation")
    graph.add_edge("check_claim_needs_substantiation", "verify_claims")
    graph.add_edge("detect_citations", "verify_claims")

    # RAG indexing edge
    if use_rag:
        graph.add_edge("prepare_documents", "index_supporting_documents")
        graph.add_edge("index_supporting_documents", "verify_claims")

    # Literature review (aim 1.a)
    if run_literature_review:
        graph.add_edge("prepare_documents", "literature_review")

    # Suggest citations (aim 2.a)
    # Must wait for ALL processing to complete before suggesting citations
    if run_suggest_citations:
        graph.add_edge("prepare_documents", "summarize_supporting_documents")
        graph.add_edge("verify_claims", "suggest_citations")
        graph.add_edge("summarize_supporting_documents", "suggest_citations")
        if run_literature_review:
            graph.add_edge("literature_review", "suggest_citations")

    # Live reports runs in parallel and is NOT dependent on suggest_citations
    # Keep it downstream of verify_claims to ensure claims/citations/references exist
    if run_live_reports:
        graph.add_edge("verify_claims", "generate_live_reports_analysis")

    # Finalize/join node to allow parallel branches to complete
    if run_suggest_citations and run_live_reports:
        graph.add_edge("suggest_citations", "finalize")
        graph.add_edge("generate_live_reports_analysis", "finalize")
        graph.set_finish_point("finalize")
    elif run_suggest_citations:
        graph.set_finish_point("suggest_citations")
    elif run_live_reports:
        graph.set_finish_point("generate_live_reports_analysis")
    else:
        graph.set_finish_point("verify_claims")

    return graph


if __name__ == "__main__":
    # Print the graph in mermaid format
    # Paste it into https://mermaid.live/ to see the graph

    workflow_graph = build_claim_substantiator_graph(
        run_literature_review=True, run_suggest_citations=True, run_live_reports=True
    )
    app = workflow_graph.compile()
    print(app.get_graph().draw_mermaid())
