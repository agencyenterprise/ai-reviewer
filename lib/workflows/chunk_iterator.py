from typing import Callable, List, Tuple, TypeVar, Any
from lib.run_utils import run_tasks
from lib.workflows.models import WorkflowError

# Type variables for generic chunk iterator
TState = TypeVar("TState")
TChunk = TypeVar("TChunk")


def get_target_chunks(state: Any) -> List[Any]:
    """
    Get target chunks from state based on configuration.

    Args:
        state: State object containing chunks and config

    Returns:
        List of chunks to process
    """
    target_chunk_indices = getattr(state.config, "target_chunk_indices", None)

    if target_chunk_indices is None:
        return state.chunks

    return [state.chunks[index] for index in target_chunk_indices]


async def iterate_chunks(
    state: TState,
    func: Callable[[TState, Any], Any],
    desc: str,
) -> dict[str, Any]:
    """
    Generic chunk iterator that works with any state and chunk types.

    Args:
        state: The workflow state object
        func: Function to apply to each chunk
        desc: Description for progress tracking

    Returns:
        Dictionary containing updated chunks and any errors
    """
    target_chunks = get_target_chunks(state)

    tasks = [func(state, chunk) for chunk in target_chunks]
    results: Tuple[List[TChunk], List[Exception]] = await run_tasks(tasks, desc=desc)
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


# Type-safe factory functions for specific state types
def create_chunk_iterator(state_type: type[TState], chunk_type: type[TChunk]):
    """
    Create a type-safe chunk iterator for specific state and chunk types.

    Args:
        state_type: The state class type (used for type checking)
        chunk_type: The chunk class type (used for type checking)

    Returns:
        A type-safe chunk iterator function

    Example:
        ClaimChunkIterator = create_chunk_iterator(ClaimSubstantiatorState, DocumentChunk)
        result = await ClaimChunkIterator(state, func, "Processing chunks")
    """
    # Use the parameters for type checking even if not used at runtime
    _ = state_type, chunk_type

    async def typed_iterate_chunks(
        state: TState,
        func: Callable[[TState, TChunk], TChunk],
        desc: str,
    ) -> dict[str, Any]:
        return await iterate_chunks(state, func, desc)

    return typed_iterate_chunks


# Backward compatibility: Specific iterator for ClaimSubstantiatorState
async def iterate_claim_chunks(
    state: Any,  # ClaimSubstantiatorState
    func: Callable[
        [Any, Any], Any
    ],  # Callable[[ClaimSubstantiatorState, DocumentChunk], DocumentChunk]
    desc: str,
) -> dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Use create_chunk_iterator() for new code.
    """
    return await iterate_chunks(state, func, desc)
