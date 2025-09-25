from typing import Callable, List, Tuple
from lib.run_utils import run_tasks
from lib.workflows.claim_substantiation.state import (
    WorkflowError,
    ClaimSubstantiatorState,
    DocumentChunk,
)


def get_target_chunks(state: ClaimSubstantiatorState) -> List[DocumentChunk]:
    target_chunk_indices = state.target_chunk_indices

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
    results: Tuple[List[DocumentChunk], List[Exception]] = await run_tasks(
        tasks, desc=desc
    )
    updated_chunks, exceptions = results

    errors = []
    for index, exception in enumerate(exceptions):
        if exception is not None:
            errors.append(
                WorkflowError(
                    task_name=func.__name__, error=str(exception), chunk_index=index
                )
            )

    return {"chunks": updated_chunks, "errors": errors}
