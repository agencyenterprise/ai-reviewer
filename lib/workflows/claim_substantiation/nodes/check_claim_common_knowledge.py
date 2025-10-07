import logging

from lib.agents.claim_common_knowledge_checker import (
    ClaimCommonKnowledgeResult,
    ClaimCommonKnowledgeResultWithClaimIndex,
    claim_common_knowledge_checker_agent,
)
from lib.agents.formatting_utils import format_audience_context, format_domain_context
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)


async def check_claim_common_knowledge(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info(f"common_knowledge ({state.config.session_id}): starting")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "common_knowledge" not in agents_to_run:
        logger.info(
            f"common_knowledge ({state.config.session_id}): Skipping claim common knowledge check (not in agents_to_run)"
        )
        return {}

    results = await iterate_chunks(
        state,
        _check_chunk_claim_common_knowledge,
        "Checking chunk claim common knowledge",
    )
    logger.info(f"common_knowledge ({state.config.session_id}): done")
    return results


async def _check_chunk_claim_common_knowledge(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    claim_common_knowledge_results = []
    for claim_index, claim in enumerate(chunk.claims.claims):
        result: ClaimCommonKnowledgeResult = (
            await claim_common_knowledge_checker_agent.apply(
                {
                    "full_document": state.file.markdown,
                    "paragraph": state.get_paragraph(chunk.paragraph_index),
                    "chunk": chunk.content,
                    "claim": claim.claim,
                    "domain_context": format_domain_context(state.config.domain),
                    "audience_context": format_audience_context(
                        state.config.target_audience
                    ),
                }
            )
        )

        claim_common_knowledge_results.append(
            ClaimCommonKnowledgeResultWithClaimIndex(
                chunk_index=chunk.chunk_index,
                claim_index=claim_index,
                **result.model_dump(),
            )
        )

    return chunk.model_copy(
        update={"claim_common_knowledge_results": claim_common_knowledge_results}
    )
