import logging
from lib.agents.claim_detector import ClaimResponse, claim_detector_agent
from lib.agents.tools import format_domain_context, format_audience_context
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)


async def detect_claims(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("detect_claims: detecting claims")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "claims" not in agents_to_run:
        logger.info("detect_claims: Skipping claims detection (not in agents_to_run)")
        return {}

    return await iterate_chunks(state, _detect_chunk_claims, "Detecting chunk claims")


async def _detect_chunk_claims(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    claims: ClaimResponse = await claim_detector_agent.apply(
        {
            "chunk": chunk.content,
            "full_document": state.file.markdown,
            "domain_context": format_domain_context(state.config.domain),
            "audience_context": format_audience_context(state.config.target_audience),
            "paragraph": state.get_paragraph(chunk.paragraph_index),
        }
    )
    return chunk.model_copy(update={"claims": claims})
