import logging
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    ClaimSubstantiationChunk,
)
from lib.agents.claim_substantiator import claim_substantiator_agent, ClaimSubstantiationResultWithClaimIndex
from lib.run_utils import run_tasks

logger = logging.getLogger(__name__)


async def substantiate_claims(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("substantiate_claims: substantiating claims")

    agents_to_run = state.get("agents_to_run")
    if agents_to_run and "substantiation" not in agents_to_run:
        logger.info("substantiate_claims: Skipping claim substantiation (not in agents_to_run)")
        return {}

    if not state.get("claims_by_chunk") or not state.get("citations_by_chunk"):
        logger.info("substantiate_claims: Missing claims or citations, skipping")
        return {}

    processor = DocumentProcessor(state["file"])
    
    supporting_files = state.get("supporting_files", [])
    references = state.get("references", [])
    
    async def process_chunk_substantiation(chunk_idx, chunk):
        try:
            claims_for_chunk = state["claims_by_chunk"][chunk_idx] if chunk_idx < len(state["claims_by_chunk"]) else None
            
            if not claims_for_chunk or not hasattr(claims_for_chunk, 'claims') or not claims_for_chunk.claims:
                logger.info(f"No claims found for substantiation in chunk {chunk_idx}")
                return []
            
            claims_to_substantiate = []
            for claim in claims_for_chunk.claims:
                needs_substantiation = (
                    getattr(claim, 'needs_substantiation', False) or 
                    getattr(claim, 'needsSubstantiation', False)
                )
                if needs_substantiation:
                    claims_to_substantiate.append(claim)
            
            if not claims_to_substantiate:
                logger.info(f"No claims need substantiation in chunk {chunk_idx}")
                return []
            
            substantiations = []
            for claim_index, claim in enumerate(claims_to_substantiate):
                try:
                    prompt_kwargs = {
                        "claim": claim.claim,
                        "cited_references": references
                    }
                    
                    result_data = await processor.apply_agent_to_chunk(
                        agent=claim_substantiator_agent,
                        chunk=chunk,
                        prompt_kwargs=prompt_kwargs
                    )
                    
                    if result_data:
                        substantiation_with_index = ClaimSubstantiationResultWithClaimIndex(
                            **result_data.model_dump(),
                            chunk_index=chunk_idx,
                            claim_index=claim_index
                        )
                        substantiations.append(substantiation_with_index)
                        
                except Exception as e:
                    logger.error(f"Error substantiating claim {claim_index} in chunk {chunk_idx}: {e}")
                    continue
            
            return substantiations
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_idx} for substantiation: {e}")
            return []
    
    def default_response():
        return ClaimSubstantiationChunk(substantiations=[])
    
    chunks = await processor.get_chunks()
    target_indices = state.get("target_chunk_indices")
    
    if target_indices is not None:
        existing_substantiations = state.get("claim_substantiations_by_chunk", [])
        while len(existing_substantiations) < len(chunks):
            existing_substantiations.append(default_response())
        chunks_to_process = [(i, chunks[i]) for i in target_indices if i < len(chunks)]
        logger.info(f"substantiate_claims: Selective processing of chunks {target_indices}")
    else:
        existing_substantiations = [default_response() for _ in range(len(chunks))]
        chunks_to_process = list(enumerate(chunks))
        logger.info(f"substantiate_claims: Full processing of {len(chunks)} chunks")
    
    import asyncio
    semaphore = asyncio.Semaphore(3)
    
    async def process_with_semaphore(chunk_idx, chunk):
        async with semaphore:
            return await process_chunk_substantiation(chunk_idx, chunk)
    
    tasks = [process_with_semaphore(chunk_idx, chunk) for chunk_idx, chunk in chunks_to_process]
    chunk_results = await run_tasks(tasks, desc="Substantiating claims")
    
    final_substantiations = existing_substantiations.copy()
    
    for (chunk_idx, _), result in zip(chunks_to_process, chunk_results):
        if isinstance(result, Exception):
            logger.error(f"Exception in chunk {chunk_idx}: {result}")
            substantiation_chunk = ClaimSubstantiationChunk(substantiations=[])
        elif isinstance(result, list):
            substantiation_chunk = ClaimSubstantiationChunk(substantiations=result)
        else:
            logger.warning(f"Unexpected result type for chunk {chunk_idx}: {type(result)}")
            substantiation_chunk = ClaimSubstantiationChunk(substantiations=[])
        
        final_substantiations[chunk_idx] = substantiation_chunk
    
    logger.info(f"substantiate_claims: Completed substantiation for {len(final_substantiations)} chunks")
    return {"claim_substantiations_by_chunk": final_substantiations}