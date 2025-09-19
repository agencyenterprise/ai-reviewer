import logging
from typing import List
from lib.agents.citation_detector import CitationResponse
from lib.agents.reference_extractor import BibliographyItem
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.agents.citation_detector import (
    citation_detector_agent,
    CitationResponse,
)

logger = logging.getLogger(__name__)


async def detect_citations(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("detect_citations: detecting citations")

    processor = DocumentProcessor(state["file"])

    bibliography = _format_bibliography_prompt_section(state.get("references", []))

    results: List[CitationResponse] = await processor.apply_agent_to_all_chunks(
        citation_detector_agent,
        prompt_kwargs={"bibliography": bibliography},
    )
    return {"citations_by_chunk": results}


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
