import logging
from lib.agents.literature_review import (
    LiteratureReviewResponse,
    literature_review_agent,
)
from lib.workflows.chunk_iterator import create_chunk_iterator
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)

iterate_claim_chunks = create_chunk_iterator(ClaimSubstantiatorState, DocumentChunk)


async def literature_review(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("literature_review: reviewing literature")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "literature_review" not in agents_to_run:
        logger.info(
            "literature_review: Skipping literature review (not in agents_to_run)"
        )
        return {}

    markdown = state.file.markdown

    literature_review_report: str = await literature_review_agent.apply(
        {
            "full_document": markdown,
            "bibliography": state.references,
        }
    )
    return {"literature_review": literature_review_report}
