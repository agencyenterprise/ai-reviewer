import logging

from lib.agents.literature_review import literature_review_agent
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


async def literature_review(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info(f"literature_review ({state.config.session_id}): starting")

    if not state.config.run_literature_review:
        logger.info(
            f"literature_review ({state.config.session_id}): skipping literature review (run_literature_review is False)"
        )
        return {}

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "literature_review" not in agents_to_run:
        logger.info(
            f"literature_review ({state.config.session_id}): Skipping literature review (not in agents_to_run)"
        )
        return {}

    markdown = state.file.markdown

    literature_review_report: str = await literature_review_agent.apply(
        {
            "full_document": markdown,
            "bibliography": state.references,
        }
    )

    logger.info(f"literature_review ({state.config.session_id}): done")
    return {"literature_review": literature_review_report}
