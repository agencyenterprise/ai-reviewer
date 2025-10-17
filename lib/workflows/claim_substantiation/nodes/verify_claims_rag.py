import logging
from typing import List

from lib.agents.claim_verifier import (
    ClaimSubstantiationResult,
    ClaimSubstantiationResultWithClaimIndex,
    RetrievedPassageInfo,
    claim_verifier_agent,
)
from lib.agents.formatting_utils import (
    format_audience_context,
    format_domain_context,
)
from lib.services.vector_store import (
    RetrievedPassage,
    get_collection_id,
    get_file_hash_from_path,
    get_vector_store_service,
)
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.workflows.decorators import handle_chunk_errors, requires_agent

logger = logging.getLogger(__name__)


def format_retrieved_passages(passages: List[RetrievedPassage]) -> str:
    """Format retrieved passages to look like cited references."""
    if not passages:
        return "No relevant passages found in supporting documents."

    formatted = []
    for i, passage in enumerate(passages, 1):
        formatted.append(
            f"[Retrieved Passage {i} from {passage.source_file}]\n"
            f"{passage.content}\n"
            f"(Similarity: {passage.similarity_score:.2f})\n"
        )
    return "\n".join(formatted)


@requires_agent("substantiation")
async def verify_claims_with_rag(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    """Verify claims using RAG to retrieve relevant passages."""
    logger.info(f"verify_claims_with_rag ({state.config.session_id}): starting")

    results = await iterate_chunks(
        state, _verify_chunk_claims_rag, "Verifying chunk claims with RAG"
    )

    logger.info(f"verify_claims_with_rag ({state.config.session_id}): done")
    return results


@handle_chunk_errors("Claim verification with RAG")
async def _verify_chunk_claims_rag(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    """Verify claims in a chunk using RAG retrieval.

    Note: RAG doesn't require citations to be detected first - it retrieves
    relevant passages directly based on the claim text.
    """

    if chunk.claims is None or not chunk.claims.claims:
        logger.debug(f"Chunk {chunk.chunk_index} has no claims")
        return chunk

    vector_store = get_vector_store_service()
    substantiations = []

    for claim_index, claim in enumerate(chunk.claims.claims):
        common_knowledge_result = next(
            (
                r
                for r in chunk.claim_common_knowledge_results
                if r.claim_index == claim_index
            ),
            None,
        )
        if common_knowledge_result and not common_knowledge_result.needs_substantiation:
            continue

        all_passages = []
        for file_doc in state.supporting_files or []:
            file_hash = get_file_hash_from_path(file_doc.file_path)
            collection_id = get_collection_id(file_hash)

            passages = await vector_store.retrieve_relevant_passages(
                query=claim.claim, collection_id=collection_id
            )
            all_passages.extend(passages)

        all_passages.sort(key=lambda p: p.similarity_score, reverse=True)
        top_passages = all_passages[:10]

        cited_references_rag = format_retrieved_passages(top_passages)

        result: ClaimSubstantiationResult = await claim_verifier_agent.apply(
            {
                "full_document": state.file.markdown,
                "paragraph": state.get_paragraph(chunk.paragraph_index),
                "chunk": chunk.content,
                "claim": claim.claim,
                "cited_references": cited_references_rag,
                "cited_references_paragraph": "",
                "domain_context": format_domain_context(state.config.domain),
                "audience_context": format_audience_context(
                    state.config.target_audience
                ),
            }
        )

        result_with_passages = result.model_copy(
            update={
                "retrieved_passages": [
                    RetrievedPassageInfo(
                        content=p.content,
                        source_file=p.source_file,
                        similarity_score=p.similarity_score,
                        chunk_index=p.chunk_index,
                    )
                    for p in top_passages
                ]
            }
        )

        substantiations.append(
            ClaimSubstantiationResultWithClaimIndex(
                chunk_index=chunk.chunk_index,
                claim_index=claim_index,
                **result_with_passages.model_dump(),
            )
        )

    return chunk.model_copy(update={"substantiations": substantiations})
