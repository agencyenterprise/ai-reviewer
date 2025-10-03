import logging
from lib.agents.citation_suggester import (
    CitationSuggestionResponse,
    CitationSuggestionResultWithClaimIndex,
    citation_suggester_agent,
)
from lib.workflows.chunk_iterator import create_chunk_iterator
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.workflows.claim_substantiation.nodes.detect_citations import (
    _format_bibliography_prompt_section,
)
from lib.agents.formatting_utils import (
    format_cited_references,
)


logger = logging.getLogger(__name__)

iterate_claim_chunks = create_chunk_iterator(ClaimSubstantiatorState, DocumentChunk)


async def suggest_citations(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("suggest_citations: suggesting citations")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "substantiation" not in agents_to_run:
        logger.info(
            "suggest_citations: Skipping citations suggestion (not in agents_to_run)"
        )
        return {}

    return await iterate_claim_chunks(
        state, _suggest_chunk_citations, "Suggesting chunk citations"
    )


async def _suggest_chunk_citations(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    citation_suggestions = []
    for claim_index, claim in enumerate(chunk.claims.claims):
        common_knowledge_result = next(
            (
                result
                for result in chunk.claim_common_knowledge_results
                if result.claim_index == claim_index
            ),
            None,
        )
        if common_knowledge_result and not common_knowledge_result.needs_substantiation:
            continue

        cited_references = format_cited_references(
            state.references,
            state.supporting_files,
            chunk.citations,
            truncate_at_character_count=1000,  # Include only a little bit of the text of the references
        )

        result: CitationSuggestionResponse = await citation_suggester_agent.apply(
            {
                "full_document": state.file.markdown,
                "bibliography": _format_bibliography_prompt_section(state.references),
                "paragraph": state.get_paragraph(chunk.paragraph_index),
                "chunk": chunk.content,
                "claim": claim.claim,
                "cited_references": cited_references,
                "literature_review_report": state.literature_review,
            }
        )
        citation_suggestions.append(
            CitationSuggestionResultWithClaimIndex(
                chunk_index=chunk.chunk_index,
                claim_index=claim_index,
                **result.model_dump(),
            )
        )

    return chunk.model_copy(update={"citation_suggestions": citation_suggestions})
