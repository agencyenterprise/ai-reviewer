import logging
from lib.agents.citation_detector import CitationResponse
from lib.agents.formatting_utils import (
    format_cited_references,
    format_domain_context,
    format_audience_context,
)
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.agents.claim_verifier import (
    ClaimSubstantiationResult,
    claim_verifier_agent,
    ClaimSubstantiationResultWithClaimIndex,
)
from lib.workflows.decorators import handle_chunk_errors, requires_agent

logger = logging.getLogger(__name__)


@requires_agent("substantiation")
async def verify_claims(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
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
    if chunk.citations is None:
        logger.debug(
            f"verify_claims: Chunk {chunk.chunk_index} has no citations detected, skipping verification"
        )
        return chunk

    if chunk.claims is None or not chunk.claims.claims:
        logger.debug(
            f"verify_claims: Chunk {chunk.chunk_index} has no claims to verify"
        )
        return chunk

    substantiations = []
    for claim_index, claim in enumerate(chunk.claims.claims):
        common_knowledge_result = next(
            (
                result
                for result in chunk.claim_common_knowledge_results
                if result.claim_index == claim_index
            ),
            None,
        )

        # Skip if the claim doesn't need substantiation and there are no citations in the chunk
        if (
            common_knowledge_result
            and not common_knowledge_result.needs_substantiation
            and chunk.citations
            and not chunk.citations.citations
        ):
            continue

        cited_references = format_cited_references(
            state.references,
            state.supporting_files,
            chunk.citations,
            truncate_at_character_count=100000,  # Basically include the whole text of the references
        )
        paragraph_chunks = state.get_paragraph_chunks(chunk.paragraph_index)
        paragraph_chunks_citations_not_in_the_chunk = [
            citation
            for other_chunk in paragraph_chunks
            if other_chunk != chunk
            and other_chunk.citations is not None
            and other_chunk.citations.citations
            for citation in other_chunk.citations.citations
            if chunk.citations is not None and citation not in chunk.citations.citations
        ]
        paragraph_other_chunk_citations = CitationResponse(
            citations=paragraph_chunks_citations_not_in_the_chunk,
            rationale="The other citations in the paragraph that are not in the chunk",
        )
        cited_references_paragraph = format_cited_references(
            state.references,
            state.supporting_files,
            paragraph_other_chunk_citations,
            truncate_at_character_count=100000,  # Basically include the whole text of the references
        )

        result: ClaimSubstantiationResult = await claim_verifier_agent.apply(
            {
                "full_document": state.file.markdown,
                "paragraph": state.get_paragraph(chunk.paragraph_index),
                "chunk": chunk.content,
                "claim": claim.claim,
                "cited_references": cited_references,
                "cited_references_paragraph": cited_references_paragraph,
                "domain_context": format_domain_context(state.config.domain),
                "audience_context": format_audience_context(
                    state.config.target_audience
                ),
            }
        )
        substantiations.append(
            ClaimSubstantiationResultWithClaimIndex(
                chunk_index=chunk.chunk_index,
                claim_index=claim_index,
                **result.model_dump(),
            )
        )

    return chunk.model_copy(update={"substantiations": substantiations})
