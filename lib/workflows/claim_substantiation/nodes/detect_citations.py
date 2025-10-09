import logging
from lib.agents.citation_detector import CitationResponse, citation_detector_agent
from lib.agents.formatting_utils import format_bibliography_prompt_section
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.workflows.decorators import handle_chunk_errors, requires_agent

logger = logging.getLogger(__name__)


@requires_agent("citations")
async def detect_citations(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info(f"detect_citations ({state.config.session_id}): starting")

    results = await iterate_chunks(
        state, _detect_chunk_citations, "Detecting chunk citations"
    )
    logger.info(f"detect_citations ({state.config.session_id}): done")
    return results


@handle_chunk_errors("Citation detection")
async def _detect_chunk_citations(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    citations: CitationResponse = await citation_detector_agent.apply(
        {
            "full_document": state.file.markdown,
            "bibliography": format_bibliography_prompt_section(state.references),
            "chunk": chunk.content,
            "feedback": "",
        }
    )
    return chunk.model_copy(update={"citations": citations})
