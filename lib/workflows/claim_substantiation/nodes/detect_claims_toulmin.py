import logging
from lib.agents.toulmin_claim_detector import ToulminClaimResponse, toulmin_claim_detector_agent
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


async def detect_claims_toulmin(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("detect_claims: detecting toulmin claims")

    agents_to_run = state.get("agents_to_run")
    if agents_to_run and "claims" not in agents_to_run:
        logger.info("detect_claims_toulmin: Skipping claims detection (not in agents_to_run)")
        return {}

    processor = DocumentProcessor(state["file"])
    
    prompt_kwargs = {}
    
    def default_response():
        return ToulminClaimResponse(claims=[], rationale="Not processed")
    
    final_claims = await processor.apply_agent_to_all_chunks(
        agent=toulmin_claim_detector_agent,
        prompt_kwargs=prompt_kwargs,
        target_chunk_indices=state.get("target_chunk_indices"),
        existing_results=state.get("claims_by_chunk"),
        default_response_factory=default_response
    )
    
    chunks = await processor.get_chunks()
    chunks_content = [chunk.page_content for chunk in chunks]
    
    return {"claims_by_chunk": final_claims, "chunks": chunks_content}