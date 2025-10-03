import logging
from lib.agents.citation_detector import CitationResponse
from lib.agents.formatting_utils import (
    format_cited_references,
    format_domain_context,
    format_audience_context,
)
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.agents.claim_common_knowledge_checker import (
    ClaimCommonKnowledgeResult,
    claim_common_knowledge_checker_agent,
    ClaimCommonKnowledgeResultWithClaimIndex,
)
from lib.workflows.claim_substantiation.nodes.substantiate_claims import (
    format_cited_references,
)

logger = logging.getLogger(__name__)


async def check_claim_common_knowledge(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("common_knowledge: checking claim common knowledge")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "common_knowledge" not in agents_to_run:
        logger.info(
            "common_knowledge: Skipping claim common knowledge check (not in agents_to_run)"
        )
        return {}

    return await iterate_chunks(
        state,
        _check_chunk_claim_common_knowledge,
        "Checking chunk claim common knowledge",
    )


async def _check_chunk_claim_common_knowledge(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    claim_common_knowledge_results = []
    for claim_index, claim in enumerate(chunk.claims.claims):
        cited_references = format_cited_references(
            state.references,
            state.supporting_files,
            chunk.citations,
            truncate_at_character_count=1000,  # Include only a little bit of the text of the references
        )
        paragraph_chunks = state.get_paragraph_chunks(chunk.paragraph_index)
        paragraph_chunks_citations_not_in_the_chunk = [
            citation
            for other_chunk in paragraph_chunks
            if other_chunk != chunk
            and other_chunk.citations
            and other_chunk.citations.citations
            for citation in other_chunk.citations.citations
            if citation not in chunk.citations.citations
        ]
        paragraph_other_chunk_citations = CitationResponse(
            citations=paragraph_chunks_citations_not_in_the_chunk,
            rationale="The other citations in the paragraph that are not in the chunk",
        )
        cited_references_paragraph = format_cited_references(
            state.references,
            state.supporting_files,
            paragraph_other_chunk_citations,
            truncate_at_character_count=1000,  # Include only a little bit of the text of the references
        )

        result: ClaimCommonKnowledgeResult = (
            await claim_common_knowledge_checker_agent.apply(
                {
                    "full_document": state.file.markdown,
                    "paragraph": state.get_paragraph(chunk.paragraph_index),
                    "chunk": chunk.content,
                    "claim": claim.claim,
                    "cited_references": cited_references,
                    "cited_references_paragraph": cited_references_paragraph,
                    "domain_context": format_domain_context(state.config.domain),
                    "audience_context": format_audience_context(
                        state.config.target_audience
                    ),
                }
            )
        )

        if len(chunk.citations.citations) > 0 and not result.needs_substantiation:
            result.needs_substantiation = True
            result.substantiation_rationale = (
                "[Reverted from False to True because there are references cited in the chunk of text so it must be substantiated. The rationale before the reversal was:] "
                + result.substantiation_rationale
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
