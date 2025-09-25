import logging
from lib.agents.citation_detector import CitationResponse
from lib.agents.tools import (
    format_supporting_documents_prompt_section,
    format_domain_context,
    format_audience_context,
)
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.agents.claim_substantiator import (
    ClaimSubstantiationResult,
    claim_substantiator_agent,
    ClaimSubstantiationResultWithClaimIndex,
)

logger = logging.getLogger(__name__)


async def substantiate_claims(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("substantiate_claims: substantiating claims")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "substantiation" not in agents_to_run:
        logger.info(
            "substantiate_claims: Skipping claim substantiation (not in agents_to_run)"
        )
        return {}

    return await iterate_chunks(
        state, _substantiate_chunk_claims, "Substantiating chunk claims"
    )


async def _substantiate_chunk_claims(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    substantiations = []
    for claim_index, claim in enumerate(chunk.claims.claims):
        if not claim.needs_substantiation:
            continue

        cited_references = _format_cited_references(state, chunk.citations)

        result: ClaimSubstantiationResult = await claim_substantiator_agent.apply(
            {
                "chunk": chunk.content,
                "full_document": state.file.markdown,
                "claim": claim.claim,
                "cited_references": cited_references,
                "domain_context": format_domain_context(state.config.domain),
                "audience_context": format_audience_context(
                    state.config.target_audience
                ),
            }
        )
        substantiations.append(
            ClaimSubstantiationResultWithClaimIndex(
                chunk_index=chunk.chunk_index,
                claim_index=claim_index,
                **result.model_dump(),
            )
        )

    return chunk.model_copy(update={"substantiations": substantiations})


def _format_cited_references(
    state: ClaimSubstantiatorState, citations: CitationResponse
) -> str:
    references = state.references
    supporting_files = state.supporting_files

    citations_with_associated_bibliography = [
        c for c in citations.citations if c.associated_bibliography
    ]

    if len(citations_with_associated_bibliography) == 0:
        return "No reference is cited as support for this claim.\n\n"

    cited_references_str = ""

    for citation in citations_with_associated_bibliography:
        bibliography_index = citation.index_of_associated_bibliography
        associated_reference = references[bibliography_index - 1]
        cited_references_str += f"""### Cited bibliography entry #{bibliography_index}
Citation text: `{citation.text}`
Bibliography entry text: `{associated_reference.text}`
"""
        if associated_reference.has_associated_supporting_document:
            supporting_file = supporting_files[
                associated_reference.index_of_associated_supporting_document - 1
            ]
            cited_references_str += format_supporting_documents_prompt_section(
                supporting_file
            )
        else:
            cited_references_str += "No associated supporting document provided by the user, so this bibliography item cannot be used to substantiate the claim\n\n"

    cited_references_str += "\n\n"

    return cited_references_str
