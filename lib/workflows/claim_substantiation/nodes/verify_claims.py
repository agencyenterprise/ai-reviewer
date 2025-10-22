import logging

from lib.agents.claim_verifier import (
    ClaimSubstantiationResultWithClaimIndex,
    claim_verifier_agent,
)
from lib.agents.formatting_utils import format_audience_context, format_domain_context
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.reference_providers import (
    CitationBasedReferenceProvider,
    RAGReferenceProvider,
    ReferenceContext,
    ReferenceProvider,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.workflows.decorators import handle_chunk_errors, requires_agent

logger = logging.getLogger(__name__)

_CITATION_PROVIDER = CitationBasedReferenceProvider()
_RAG_PROVIDER = RAGReferenceProvider()


def _needs_substantiation(chunk: DocumentChunk, claim_index: int) -> bool:
    """Check if a claim needs substantiation.

    A claim needs substantiation if:
    1. It has citations in the chunk that need to be verified (regardless of common knowledge status)
    2. OR it's not common knowledge and needs supporting evidence
    """

    if chunk.citations and chunk.citations.citations:
        return True

    common_knowledge_result = next(
        (
            r
            for r in chunk.claim_common_knowledge_results
            if r.claim_index == claim_index
        ),
        None,
    )
    return not common_knowledge_result or common_knowledge_result.needs_substantiation


async def _verify_chunk_claims_with_provider(
    state: ClaimSubstantiatorState,
    chunk: DocumentChunk,
    reference_provider: ReferenceProvider,
) -> DocumentChunk:
    """Verify chunk claims using the provided reference provider.

    Skips chunks with no claims. For each claim:
    - ALWAYS verifies if the chunk has citations (even if common knowledge)
    - Verifies if the claim needs substantiation (not common knowledge)

    This ensures all citations are validated regardless of common knowledge status.
    """
    if chunk.claims is None or not chunk.claims.claims:
        logger.debug(f"Chunk {chunk.chunk_index} has no claims")
        return chunk

    substantiations = []

    for claim_index, claim in enumerate(chunk.claims.claims):
        if not _needs_substantiation(chunk, claim_index):
            continue

        ref_context = await reference_provider.get_references_for_claim(
            state, chunk, claim, claim_index
        )

        is_rag_mode = ref_context.retrieved_passages is not None

        evidence_explanation = (
            "### Evidence Retrieval Method: RAG (Retrieval-Augmented Generation)\n"
            "The supporting evidence below consists of **relevant passages retrieved via semantic search** from the supporting documents. "
            "These passages were selected based on their semantic similarity to the claim. "
            "Evaluate whether these retrieved passages provide sufficient support for the claim."
            if is_rag_mode
            else "### Evidence Retrieval Method: Citation-Based\n"
            "The supporting evidence below consists of **complete supporting documents** that are cited in the text. "
            "Review the full documents to determine if they support the claim."
        )

        result = await claim_verifier_agent.apply(
            {
                "full_document": state.file.markdown,
                "paragraph": state.get_paragraph(chunk.paragraph_index),
                "chunk": chunk.content,
                "claim": claim.claim,
                "evidence_context_explanation": evidence_explanation,
                "cited_references": ref_context.cited_references,
                "cited_references_paragraph": ref_context.cited_references_paragraph,
                "domain_context": format_domain_context(state.config.domain),
                "audience_context": format_audience_context(
                    state.config.target_audience
                ),
            }
        )

        if ref_context.retrieved_passages:
            result = result.model_copy(
                update={"retrieved_passages": ref_context.retrieved_passages}
            )

        substantiations.append(
            ClaimSubstantiationResultWithClaimIndex(
                chunk_index=chunk.chunk_index,
                claim_index=claim_index,
                **result.model_dump(),
            )
        )

    return chunk.model_copy(update={"substantiations": substantiations})


@requires_agent("substantiation")
async def verify_claims(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    """Verify claims using citation-based references."""
    logger.info(f"verify_claims ({state.config.session_id}): starting")

    results = await iterate_chunks(
        state, _verify_chunk_claims, "Verifying chunk claims"
    )
    logger.info(f"verify_claims ({state.config.session_id}): done")
    return results


@handle_chunk_errors("Claim verification")
async def _verify_chunk_claims(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    """Verify claims using citation-based references."""
    if chunk.citations is None:
        logger.debug(
            f"verify_claims: Chunk {chunk.chunk_index} has no citations detected, skipping verification"
        )
        return chunk

    return await _verify_chunk_claims_with_provider(state, chunk, _CITATION_PROVIDER)


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
    """Verify claims using RAG-based references.

    RAG retrieves relevant passages directly based on claim text,
    without requiring citations to be detected first.
    """
    return await _verify_chunk_claims_with_provider(state, chunk, _RAG_PROVIDER)
