import logging
from lib.agents.tools import format_supporting_documents_prompt_section
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.agents.reference_extractor import (
    reference_extractor_agent,
    ReferenceExtractorResponse,
)

logger = logging.getLogger(__name__)


async def extract_references(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("extract_references: extracting references")

    markdown = await state["file"].get_markdown()
    supporting_documents = "\n\n".join(
        [
            f"""### Supporting document #{index + 1} (index: {index+1})
{await format_supporting_documents_prompt_section(doc, truncate_at_character_count=1000)}
"""
            for index, doc in enumerate(state.get("supporting_files", []) or [])
        ]
    )
    res: ReferenceExtractorResponse = await reference_extractor_agent.apply(
        {"full_document": markdown, "supporting_documents": supporting_documents}
    )
    return {"references": res.references}
