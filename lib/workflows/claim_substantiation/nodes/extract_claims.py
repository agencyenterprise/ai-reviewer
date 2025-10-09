import logging
from lib.agents.claim_extractor import ClaimResponse, claim_extractor_agent
from lib.agents.formatting_utils import format_domain_context, format_audience_context
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.workflows.decorators import handle_chunk_errors, requires_agent

logger = logging.getLogger(__name__)


@requires_agent("claims")
async def extract_claims(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info(f"extract_claims ({state.config.session_id}): starting")

    results = await iterate_chunks(
        state, _extract_chunk_claims, "Extracting chunk claims"
    )
    logger.info(f"extract_claims ({state.config.session_id}): done")
    return results


@handle_chunk_errors("Claim extraction")
async def _extract_chunk_claims(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    claims: ClaimResponse = await claim_extractor_agent.apply(
        {
            "chunk": chunk.content,
            "full_document": state.file.markdown,
            "domain_context": format_domain_context(state.config.domain),
            "audience_context": format_audience_context(state.config.target_audience),
            "paragraph": state.get_paragraph(chunk.paragraph_index),
        }
    )
    return chunk.model_copy(update={"claims": claims})
