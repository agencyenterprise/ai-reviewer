from typing import Callable, List
from lib.run_utils import run_tasks
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)


def get_target_chunks(state: ClaimSubstantiatorState) -> List[DocumentChunk]:
    target_chunk_indices = state.config.target_chunk_indices

    if target_chunk_indices is None:
        return state.chunks

    return [state.chunks[index] for index in target_chunk_indices]


async def iterate_chunks(
    state: ClaimSubstantiatorState,
    func: Callable[[ClaimSubstantiatorState, DocumentChunk], DocumentChunk],
    desc: str,
) -> ClaimSubstantiatorState:
    target_chunks = get_target_chunks(state)

    tasks = [func(state, chunk) for chunk in target_chunks]
    updated_chunks: List[DocumentChunk] = await run_tasks(tasks, desc=desc)

    return {"chunks": updated_chunks}
