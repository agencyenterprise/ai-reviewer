import logging

from lib.agents.claim_verifier import (
    ClaimSubstantiationResult,
    ClaimSubstantiationResultWithClaimIndex,
    claim_verifier_agent,
)
from lib.agents.formatting_utils import format_audience_context, format_domain_context
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.reference_providers import (
    CitationBasedReferenceProvider,
    RAGReferenceProvider,
    ReferenceProvider,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.workflows.decorators import handle_chunk_errors, requires_agent

logger = logging.getLogger(__name__)


async def _verify_chunk_claims_with_provider(
    state: ClaimSubstantiatorState,
    chunk: DocumentChunk,
    reference_provider: ReferenceProvider,
) -> DocumentChunk:
    """Claim verification using a reference provider.

    This function contains the core verification logic shared by both
    citation-based and RAG-based verification approaches.
    """
    if chunk.claims is None or not chunk.claims.claims:
        logger.debug(f"Chunk {chunk.chunk_index} has no claims")
        return chunk

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

        cited_refs, cited_refs_paragraph, retrieved_passages = (
            await reference_provider.get_references_for_claim(
                state, chunk, claim, claim_index
            )
        )

        result: ClaimSubstantiationResult = await claim_verifier_agent.apply(
            {
                "full_document": state.file.markdown,
                "paragraph": state.get_paragraph(chunk.paragraph_index),
                "chunk": chunk.content,
                "claim": claim.claim,
                "cited_references": cited_refs,
                "cited_references_paragraph": cited_refs_paragraph,
                "domain_context": format_domain_context(state.config.domain),
                "audience_context": format_audience_context(
                    state.config.target_audience
                ),
            }
        )

        # We must add retrieved passages if available (RAG only)
        if retrieved_passages:
            result = result.model_copy(
                update={"retrieved_passages": retrieved_passages}
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

    provider = CitationBasedReferenceProvider()
    return await _verify_chunk_claims_with_provider(state, chunk, provider)


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

    Note: RAG doesn't require citations to be detected first - it retrieves
    relevant passages directly based on the claim text.
    """
    provider = RAGReferenceProvider()
    return await _verify_chunk_claims_with_provider(state, chunk, provider)
