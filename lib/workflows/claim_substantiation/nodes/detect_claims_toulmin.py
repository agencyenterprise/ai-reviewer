import logging
from lib.agents.toulmin_claim_detector import (
    ToulminClaimResponse,
    toulmin_claim_detector_agent,
)
from lib.agents.tools import format_domain_context, format_audience_context
from lib.workflows.chunk_iterator import create_chunk_iterator, iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)

iterate_claim_chunks = create_chunk_iterator(ClaimSubstantiatorState, DocumentChunk)


async def detect_claims_toulmin(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("detect_claims: detecting toulmin claims")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "claims" not in agents_to_run:
        logger.info(
            "detect_claims_toulmin: Skipping claims detection (not in agents_to_run)"
        )
        return {}

    return await iterate_claim_chunks(
        state, _detect_chunk_claims_toulmin, "Detecting chunk claims (Toulmin)"
    )


async def _detect_chunk_claims_toulmin(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    claims: ToulminClaimResponse = await toulmin_claim_detector_agent.apply(
        {
            "chunk": chunk.content,
            "full_document": state.file.markdown,
            "domain_context": format_domain_context(state.config.domain),
            "audience_context": format_audience_context(state.config.target_audience),
            "paragraph": state.get_paragraph(chunk.paragraph_index),
        }
    )
    return chunk.model_copy(update={"claims": claims})
