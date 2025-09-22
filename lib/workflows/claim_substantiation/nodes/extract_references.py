import logging
from lib.agents.tools import format_supporting_documents_prompt_section_multiple
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.agents.reference_extractor import (
    reference_extractor_agent,
    ReferenceExtractorResponse,
)

logger = logging.getLogger(__name__)


async def extract_references(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("extract_references: extracting references")

    agents_to_run = state.agents_to_run
    if agents_to_run and "references" not in agents_to_run:
        logger.info(
            "extract_references: Skipping reference extraction (not in agents_to_run)"
        )
        return {}

    markdown = state.file.markdown
    supporting_documents = format_supporting_documents_prompt_section_multiple(
        state.supporting_files, truncate_at_character_count=1000
    )
    res: ReferenceExtractorResponse = await reference_extractor_agent.apply(
        {"full_document": markdown, "supporting_documents": supporting_documents}
    )
    return {"references": res.references}
