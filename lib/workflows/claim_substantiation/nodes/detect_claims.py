from typing import List
from lib.agents.claim_detector import claim_detector_agent, ClaimResponse
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState


async def detect_claims(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    processor = DocumentProcessor(state["file"])
    results: List[ClaimResponse] = await processor.apply_agent_to_all_chunks(
        claim_detector_agent
    )
    return {"claims_by_chunk": results}
