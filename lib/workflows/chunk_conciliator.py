from typing import List, TypeVar, Type, Callable
from lib.agents.models import ChunkWithIndex

# Type variable for any class that inherits from ChunkWithIndex
T = TypeVar("T", bound=ChunkWithIndex)


def _conciliate_chunks_generic(
    a: List[T],
    b: List[T],
    chunk_class: Type[T],
) -> List[T]:
    """
    Generic conciliation function for chunks by merging their properties.

    Args:
        a: First list of chunks (existing state)
        b: Second list of chunks (new updates)
        chunk_class: The class type to instantiate for merged chunks

    Returns:
        Merged list of chunks with combined properties
    """

    # Create a dictionary for quick lookup of chunks by index
    chunks_by_index = {chunk.chunk_index: chunk for chunk in a}

    # Merge updates from b into the existing chunks
    for updated_chunk in b:
        if updated_chunk is None:
            # in case chunk processing errored, a None is returned here so we skip the result
            continue

        existing_chunk = chunks_by_index.get(updated_chunk.chunk_index)
        if existing_chunk is None:
            # If chunk doesn't exist in a, add it
            chunks_by_index[updated_chunk.chunk_index] = updated_chunk
        else:
            # Merge the chunks by updating non-None fields from updated_chunk
            merged_data = existing_chunk.model_dump()

            # Update fields that are not None in the updated chunk
            for field, value in updated_chunk.model_dump().items():
                if value is not None:
                    merged_data[field] = value

            # Create the merged chunk using the provided class type
            chunks_by_index[updated_chunk.chunk_index] = chunk_class(**merged_data)

    # Return chunks in order by chunk_index
    return [chunks_by_index[i] for i in sorted(chunks_by_index.keys())]


def create_conciliator(chunk_class: Type[T]) -> Callable[[List[T], List[T]], List[T]]:
    """
    Create a conciliator function for a specific chunk class.

    This is the recommended way to create type-safe conciliators for specific
    chunk types that inherit from ChunkWithIndex.

    Args:
        chunk_class: The class type to instantiate for merged chunks

    Returns:
        A conciliator function that can be used as a LangGraph reducer

    Example:
        DocumentChunkConciliator = create_conciliator(DocumentChunk)
        # Use DocumentChunkConciliator as a LangGraph reducer
    """

    def conciliator(a: List[T], b: List[T]) -> List[T]:
        return _conciliate_chunks_generic(a, b, chunk_class)

    return conciliator
