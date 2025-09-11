from typing import List
from lib.agents.citation_detector import CitationResponse
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.agents.citation_detector import (
    citation_detector_agent,
    CitationResponse,
)


async def detect_citations(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    processor = DocumentProcessor(state["file"])
    bibliography = ""
    for index, reference in enumerate(state.get("references", [])):
        bibliography += f"""### Bibliography entry #{index + 1}
{reference}\n\n"""
    results: List[CitationResponse] = await processor.apply_agent_to_all_chunks(
        citation_detector_agent,
        prompt_kwargs={"bibliography": bibliography},
    )
    return {"citations_by_chunk": results}
