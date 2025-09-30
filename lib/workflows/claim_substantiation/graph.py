from pdb import run
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import Checkpointer

from lib.config.env import config
from lib.config.langfuse import langfuse_handler
from lib.workflows.claim_substantiation.nodes.prepare_documents import prepare_documents
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

    run_literature_review = False

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
    graph.add_node("substantiate_claims", substantiate_claims, defer=True)

    graph.set_entry_point("prepare_documents")

    graph.add_edge("prepare_documents", "split_into_chunks")
    if run_literature_review:
        graph.add_edge("prepare_documents", "literature_review")

    graph.add_edge("split_into_chunks", "extract_references")
    graph.add_edge("split_into_chunks", "detect_claims")

    graph.add_edge("extract_references", "detect_citations")

    # substantiate claims when both claims and citations are present
    graph.add_edge("detect_citations", "substantiate_claims")
    graph.add_edge("detect_claims", "substantiate_claims")

    graph.set_finish_point("substantiate_claims")

    # Suggest citations (aim 2.a)
    if run_suggest_citations:
        graph.add_edge("substantiate_claims", "suggest_citations")
        if run_literature_review:
            graph.add_edge("literature_review", "suggest_citations")

        graph.set_finish_point("suggest_citations")

    return graph


if __name__ == "__main__":
    # Print the graph in mermaid format
    # Paste it into https://mermaid.live/ to see the graph

    graph = build_claim_substantiator_graph()
    app = graph.compile()
    print(app.get_graph().draw_mermaid())
