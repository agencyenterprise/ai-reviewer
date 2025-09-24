import logging
from lib.agents.toulmin_claim_detector import (
    ToulminClaimResponse,
    toulmin_claim_detector_agent,
)
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)


async def detect_claims_toulmin(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("detect_claims: detecting toulmin claims")

    agents_to_run = state.agents_to_run
    if agents_to_run and "claims" not in agents_to_run:
        logger.info(
            "detect_claims_toulmin: Skipping claims detection (not in agents_to_run)"
        )
        return {}

    return await iterate_chunks(
        state, _detect_chunk_claims_toulmin, "Detecting chunk claims (Toulmin)"
    )


async def _detect_chunk_claims_toulmin(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    claims: ToulminClaimResponse = await toulmin_claim_detector_agent.apply(
        {
            "full_document": state.file.markdown,
            "paragraph": state.get_paragraph(chunk.paragraph_index),
            "chunk": chunk.content,
        }
    )
    return chunk.model_copy(update={"claims": claims})
