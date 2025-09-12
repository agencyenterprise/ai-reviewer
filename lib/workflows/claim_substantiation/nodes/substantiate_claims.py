import logging
from lib.agents.tools import format_supporting_documents_prompt_section
from lib.run_utils import run_tasks
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.agents.claim_substantiator import claim_substantiator_agent

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
    full_document = await state["file"].get_markdown()
    supporting_files = state.get("supporting_files", [])

    references = state.get("references", [])
    # Find all unsubstantiated claims
    tasks = []
    chunk_indices_with_tasks = []
    for chunk_index, (chunk, chunk_claims, citations) in enumerate(
        zip(chunks, state["claims_by_chunk"], state["citations_by_chunk"])
    ):
        unsubstantiated_claims = [
            c for c in chunk_claims.claims if c.needs_substantiation
        ]
        if unsubstantiated_claims:
            associated_bibliography_indices = [
                c.index_of_associated_bibliography
                for c in citations.citations
                if c.associated_bibliography
            ]
            claims_str = ""
            for index, claim in enumerate(unsubstantiated_claims):
                claims_str += f"### Claim #{index + 1}\n{claim.text}\n\n"
            cited_references_str = ""
            for bibliography_index in associated_bibliography_indices:
                associated_reference = references[bibliography_index - 1]
                cited_references_str += f"""### Cited bibliography entry #{bibliography_index}
Bibliography entry text: {associated_reference.text}
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

                tasks.append(
                    claim_substantiator_agent.apply(
                        {
                            "full_document": full_document,
                            "chunk": chunk.page_content,
                            "claim": claims_str,
                            "cited_references": cited_references_str,
                        }
                    )
                )
                chunk_indices_with_tasks.append(chunk_index)

    chunk_results = await run_tasks(
        tasks, desc="Processing chunks with Claim Substantiator"
    )
    claim_substantiations_by_chunk = [[] for _ in range(len(chunks))]
    for chunk_index, result in zip(chunk_indices_with_tasks, chunk_results):
        claim_substantiations_by_chunk[chunk_index].append(result)

    return {"claim_substantiations_by_chunk": claim_substantiations_by_chunk}
