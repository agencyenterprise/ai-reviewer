import logging
from lib.agents.citation_detector import CitationResponse, citation_detector_agent
from typing import List
from lib.agents.reference_extractor import BibliographyItem
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


async def detect_citations(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("detect_citations: detecting citations")

    agents_to_run = state.get("agents_to_run")
    if agents_to_run and "citations" not in agents_to_run:
        logger.info("detect_citations: Skipping citations detection (not in agents_to_run)")
        return {}

    processor = DocumentProcessor(state["file"])

    bibliography = _format_bibliography_prompt_section(state.get("references", []))

    prompt_kwargs = {
        "bibliography": bibliography
    }
    
    def default_response():
        return CitationResponse(citations=[], rationale="Not processed")
    
    final_citations = await processor.apply_agent_to_all_chunks(
        agent=citation_detector_agent,
        prompt_kwargs=prompt_kwargs,
        target_chunk_indices=state.get("target_chunk_indices"),
        existing_results=state.get("citations_by_chunk"),
        default_response_factory=default_response
    )
    
    return {"citations_by_chunk": final_citations}

def _format_bibliography_item_prompt_section(index: int, item: BibliographyItem) -> str:
    return f"""### Bibliography entry #{index + 1}
{item.text}"""


def _format_bibliography_prompt_section(references: List[BibliographyItem]) -> str:
    return "\n\n".join(
        [
            _format_bibliography_item_prompt_section(index, item)
            for index, item in enumerate(references)
        ]
    )