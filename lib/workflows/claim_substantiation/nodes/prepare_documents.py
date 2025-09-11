import logging
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


async def prepare_documents(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    # Touch markdown for main and supporting docs to ensure they are loaded/cached

    logger.info("prepare_documents: preparing documents")

    await state["file"].get_markdown()
    for supporting_file in state.get("supporting_files", []) or []:
        await supporting_file.get_markdown()
    return {}
