import logging
from lib.agents.tools import format_supporting_documents_prompt_section
from lib.run_utils import run_tasks
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.agents.claim_substantiator import (
    ClaimSubstantiationResultWithClaimIndex,
    claim_substantiator_agent,
)

logger = logging.getLogger(__name__)


async def substantiate_claims(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("substantiate_claims: substantiating claims")

    # Require claims and citations to be present
    if not state.get("claims_by_chunk") or not state.get("citations_by_chunk"):
        return {}

    processor = DocumentProcessor(state["file"])
    chunks = await processor.get_chunks()
    full_document = state["file"].markdown
    supporting_files = state.get("supporting_files", [])

    references = state.get("references", [])
    # Find all unsubstantiated claims
    tasks = []
    chunk_claim_indices_of_tasks = []
    for chunk_index, (chunk, chunk_claims, citations) in enumerate(
        zip(chunks, state["claims_by_chunk"], state["citations_by_chunk"])
    ):
        for claim_index, claim in enumerate(chunk_claims.claims):
            if not claim.needs_substantiation:
                continue
            unsubstantiated_claim = claim
            citations_with_associated_bibliography = [
                c for c in citations.citations if c.associated_bibliography
            ]
            claim_str = f"""### The claim that we are investigating
Claim: `{unsubstantiated_claim.text}`
Rationale for why the text chunk implies this claim: `{unsubstantiated_claim.rationale}`
"""
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
                    cited_references_str += (
                        await format_supporting_documents_prompt_section(
                            supporting_file
                        )
                    )
                else:
                    cited_references_str += "No associated supporting document provided by the user, so this bibliography item cannot be used to substantiate the claim\n\n"

                cited_references_str += "\n\n"

            if len(citations_with_associated_bibliography) == 0:
                cited_references_str = (
                    "No reference is cited as support for this claim.\n\n"
                )
                # TODO: also evaluate claims that provide no reference. This can be done without an agent really, so may not go here.
                continue

            tasks.append(
                claim_substantiator_agent.apply(
                    {
                        "full_document": full_document,
                        "chunk": chunk.page_content,
                        "claim": claim_str,
                        "cited_references": cited_references_str,
                    }
                )
            )
            chunk_claim_indices_of_tasks.append((chunk_index, claim_index))

    chunk_results = await run_tasks(
        tasks, desc="Processing chunks with Claim Substantiator"
    )
    claim_substantiations_by_chunk = [[] for _ in range(len(chunks))]
    for (chunk_index, claim_index), result in zip(
        chunk_claim_indices_of_tasks, chunk_results
    ):
        result_with_claim_index = ClaimSubstantiationResultWithClaimIndex(
            chunk_index=chunk_index, claim_index=claim_index, **result.model_dump()
        )
        claim_substantiations_by_chunk[chunk_index].append(result_with_claim_index)

    return {"claim_substantiations_by_chunk": claim_substantiations_by_chunk}
