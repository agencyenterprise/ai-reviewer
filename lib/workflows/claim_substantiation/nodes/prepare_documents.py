import logging

from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


async def prepare_documents(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info(f"prepare_documents ({state.config.session_id}): starting")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "prepare_documents" not in agents_to_run:
        logger.info(
            f"prepare_documents ({state.config.session_id}): Skipping prepare_documents (not in agents_to_run)"
        )
        return {}

    logger.info(f"prepare_documents ({state.config.session_id}): done")

    return {}
