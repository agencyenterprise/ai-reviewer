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

    markdown = state["file"].markdown
    supporting_documents = await format_supporting_documents_prompt_section_multiple(
        state.get("supporting_files", []) or [], truncate_at_character_count=1000
    )
    res: ReferenceExtractorResponse = await reference_extractor_agent.apply(
        {"full_document": markdown, "supporting_documents": supporting_documents}
    )
    return {"references": res.references}
