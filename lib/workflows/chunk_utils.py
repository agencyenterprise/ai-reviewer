from typing import TYPE_CHECKING, List, Optional, Sequence, cast

from lib.agents.models import ChunkWithIndex
from lib.workflows.chunk_splitting.state import ChunkSplittingState
from lib.workflows.models import WorkflowRunType
from lib.workflows.util import get_state_by_type

if TYPE_CHECKING:
    from lib.workflows.workflow_types import WorkflowState


class AnalyzedChunk(ChunkWithIndex):
    """A document chunk, carrying its index and line range.

    Previously also carried claim-extraction, categorization, and
    citation-detection results. Those workflows were removed and nothing ever
    read the enriched fields — the only consumer, the docx export, uses chunks
    solely to resolve an issue's line range.
    """


def build_analyzed_chunks(
    existing_states: List["WorkflowState"],
) -> List[AnalyzedChunk]:
    """Build AnalyzedChunk objects from the chunk splitting state.

    Args:
        existing_states: List of workflow states from dependency workflows

    Returns:
        The document's chunks, or an empty list if chunk splitting has not run.
    """
    chunk_splitting_state_raw = get_state_by_type(
        WorkflowRunType.CHUNK_SPLITTING, existing_states
    )
    if chunk_splitting_state_raw is None:
        return []

    chunk_splitting_state = cast(ChunkSplittingState, chunk_splitting_state_raw)

    return [
        AnalyzedChunk(
            content=doc_chunk.content,
            chunk_index=doc_chunk.chunk_index,
            paragraph_index=doc_chunk.paragraph_index,
            headings=doc_chunk.headings,
            start_line=doc_chunk.start_line,
            end_line=doc_chunk.end_line,
        )
        for doc_chunk in chunk_splitting_state.chunks
    ]


def find_chunk_index_by_text(
    chunks: Sequence[ChunkWithIndex], text: str
) -> Optional[int]:
    """Find the chunk index of the first chunk that contains the given text."""

    for chunk in chunks:
        if text in chunk.content:
            return chunk.chunk_index

    return None


def find_chunk_by_index(
    chunks: List[AnalyzedChunk], chunk_index: int
) -> Optional[AnalyzedChunk]:
    """Find a chunk by its index."""
    for chunk in chunks:
        if chunk.chunk_index == chunk_index:
            return chunk
    return None
