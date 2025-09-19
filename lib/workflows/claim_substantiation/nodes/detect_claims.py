import asyncio
import logging
from typing import List
from lib.agents.claim_detector import ClaimResponse
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


async def detect_claims(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("detect_claims: detecting claims")

    # Skip this node if not in agents_to_run
    agents_to_run = state.get("agents_to_run")
    if agents_to_run and "claims" not in agents_to_run:
        logger.info("detect_claims: Skipping claims detection (not in agents_to_run)")
        return {}

    # Get document chunks using DocumentProcessor
    processor = DocumentProcessor(state["file"])
    chunks = await processor.get_chunks()
    
    # Determine which chunks to process
    target_indices = state.get("target_chunk_indices")
    if target_indices is not None:
        # Selective processing - preserve existing results
        existing_claims = state.get("claims_by_chunk", [])
        # Ensure we have enough existing results, pad with empty responses if needed
        while len(existing_claims) < len(chunks):
            existing_claims.append(ClaimResponse(claims=[], rationale="Not processed"))
        chunks_to_process = [(i, chunks[i]) for i in target_indices if i < len(chunks)]
        logger.info(f"detect_claims: Selective processing of chunks {target_indices}")
    else:
        # Full processing
        existing_claims = [ClaimResponse(claims=[], rationale="Not processed")] * len(chunks)
        chunks_to_process = list(enumerate(chunks))
        logger.info(f"detect_claims: Full processing of {len(chunks)} chunks")
    
    # Apply claims agent to selected chunks directly using DocumentProcessor
    from lib.agents.claim_detector import claim_detector_agent
    
    # Process selected chunks concurrently
    semaphore = asyncio.Semaphore(3)  # Limit concurrency
    
    async def process_chunk(chunk_idx, chunk):
        async with semaphore:
            try:
                # Use DocumentProcessor's apply_agent_to_chunk method
                result_data = await processor.apply_agent_to_chunk(
                    agent=claim_detector_agent,
                    chunk=chunk,
                    prompt_kwargs={"use_toulmin": False}
                )
                return result_data
            except Exception as e:
                logger.error(f"Error processing chunk {chunk_idx}: {e}")
                # Return empty response on error
                return ClaimResponse(claims=[], rationale=f"Error processing chunk: {e}")
    
    # Process selected chunks
    tasks = [process_chunk(chunk_idx, chunk) for chunk_idx, chunk in chunks_to_process]
    chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Merge results back into full results array
    final_claims = existing_claims.copy()
    
    for (chunk_idx, _), result in zip(chunks_to_process, chunk_results):
        if isinstance(result, Exception):
            logger.error(f"Exception in chunk {chunk_idx}: {result}")
            final_claims[chunk_idx] = ClaimResponse(claims=[], rationale=f"Error processing chunk: {result}")
        elif isinstance(result, ClaimResponse):
            final_claims[chunk_idx] = result
        else:
            logger.warning(f"Unexpected result type for chunk {chunk_idx}: {type(result)}")
            final_claims[chunk_idx] = ClaimResponse(claims=[], rationale="Unexpected result type")
    
    chunks_content = [chunk.page_content for chunk in chunks]
    return {"claims_by_chunk": final_claims, "chunks": chunks_content}