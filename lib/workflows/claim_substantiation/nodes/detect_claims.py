import logging
from lib.agents.claim_detector import ClaimResponse, claim_detector_agent
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)


async def detect_claims(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("detect_claims: detecting claims")

    agents_to_run = state.get("agents_to_run")
    if agents_to_run and "claims" not in agents_to_run:
        logger.info("detect_claims: Skipping claims detection (not in agents_to_run)")
        return {}

    processor = DocumentProcessor(state["file"])

    prompt_kwargs = {"use_toulmin": False}

    def default_response():
        return ClaimResponse(claims=[], rationale="Not processed")

    final_claims = await processor.apply_agent_to_all_chunks(
        agent=claim_detector_agent,
        prompt_kwargs=prompt_kwargs,
        target_chunk_indices=state.get("target_chunk_indices"),
        existing_results=state.get("claims_by_chunk"),
        default_response_factory=default_response,
    )

    return {
        "chunks": [
            state["chunks"][index].model_copy(update={"claims": claims})
            for index, claims in enumerate(final_claims)
        ],
    }
