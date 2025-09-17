import logging
from typing import List
from lib.agents.claim_detector import claim_detector_agent, ClaimResponse
from lib.agents.toulmin_claim_detector import (
    toulmin_claim_detector_agent,
    ToulminClaimResponse,
)
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


async def detect_claims_toulmin(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("detect_claims: detecting claims")

    processor = DocumentProcessor(state["file"])
    results: List[ToulminClaimResponse] = await processor.apply_agent_to_all_chunks(
        toulmin_claim_detector_agent
    )
    chunks = [chunk.page_content for chunk in await processor.get_chunks()]
    return {"claims_by_chunk": results, "chunks": chunks}
