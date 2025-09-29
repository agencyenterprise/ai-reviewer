import logging
from lib.agents.literature_review import literature_review_agent
from typing import List
from lib.agents.reference_extractor import BibliographyItem
from lib.workflows.chunk_iterator import create_chunk_iterator, iterate_chunks
from lib.workflows.citation_suggestion.state import (
    CitationSuggestionState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)

iterate_claim_chunks = create_chunk_iterator(CitationSuggestionState, DocumentChunk)


async def perform_literature_review(
    state: CitationSuggestionState,
) -> CitationSuggestionState:
    logger.info("perform_literature_review: performing literature review")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "literature_review" not in agents_to_run:
        logger.info(
            "perform_literature_review: Skipping literature review (not in agents_to_run)"
        )
        return {}

    return await iterate_chunks(
        state, _detect_chunk_citations, "Detecting chunk citations"
    )


async def _detect_chunk_citations(
    state: CitationSuggestionState, chunk: DocumentChunk
) -> DocumentChunk:
    citations: CitationResponse = await citation_detector_agent.apply(
        {
            "full_document": state.file.markdown,
            "bibliography": _format_bibliography_prompt_section(state.references),
            "chunk": chunk.content,
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
