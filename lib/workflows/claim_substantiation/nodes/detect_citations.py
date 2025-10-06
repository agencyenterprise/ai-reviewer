import logging
from lib.agents.citation_detector import CitationResponse, citation_detector_agent
from typing import Dict, List, Optional
from lib.agents.formatting_utils import format_bibliography_prompt_section
from lib.agents.reference_extractor import BibliographyItem
from lib.agents.document_summarizer import DocumentSummary
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)


async def detect_citations(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info(f"detect_citations ({state.config.session_id}): starting")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "citations" not in agents_to_run:
        logger.info(
            f"detect_citations ({state.config.session_id}): Skipping citations detection (not in agents_to_run)"
        )
        return {}

    results = await iterate_chunks(
        state, _detect_chunk_citations, "Detecting chunk citations"
    )
    logger.info(f"detect_citations ({state.config.session_id}): done")
    return results


async def _detect_chunk_citations(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    citations: CitationResponse = await citation_detector_agent.apply(
        {
            "full_document": state.file.markdown,
            "bibliography": format_bibliography_prompt_section(state.references),
            "chunk": chunk.content,
        }
    )
    return chunk.model_copy(update={"citations": citations})
