import logging
from lib.agents.citation_detector import CitationResponse, citation_detector_agent
from typing import List
from lib.agents.reference_extractor import BibliographyItem
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)


async def detect_citations(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("detect_citations: detecting citations")

    agents_to_run = state.agents_to_run
    if agents_to_run and "citations" not in agents_to_run:
        logger.info(
            "detect_citations: Skipping citations detection (not in agents_to_run)"
        )
        return {}

    return await iterate_chunks(
        state, _detect_chunk_citations, "Detecting chunk citations"
    )


async def _detect_chunk_citations(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    citations: CitationResponse = await citation_detector_agent.apply(
        {
            "chunk": chunk.content,
            "full_document": state.file.markdown,
            "bibliography": _format_bibliography_prompt_section(state.references),
        }
    )
    return chunk.model_copy(update={"citations": citations})


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
