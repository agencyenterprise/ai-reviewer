from typing import Annotated, List, Optional, Dict, Any
from pydantic import BaseModel, Field

from lib.agents.citation_detector import CitationResponse
from lib.agents.claim_detector import ClaimResponse
from lib.agents.toulmin_claim_detector import ToulminClaimResponse
from lib.agents.reference_extractor import BibliographyItem
from lib.agents.claim_substantiator import ClaimSubstantiationResultWithClaimIndex
from lib.services.file import FileDocument


class DocumentChunk(BaseModel):
    """Independent chunk response object with all processing results"""

    content: str
    chunk_index: int

    claims: Optional[ClaimResponse | ToulminClaimResponse] = None
    citations: Optional[CitationResponse] = None
    substantiations: List[ClaimSubstantiationResultWithClaimIndex] = []


def conciliate_chunks(
    a: List[DocumentChunk], b: List[DocumentChunk]
) -> List[DocumentChunk]:
    """
    Conciliate two lists of DocumentChunk by merging their properties.

    This reducer function is used by LangGraph to handle multiple updates to the same
    chunks field from different nodes running in parallel.

    Args:
        a: First list of DocumentChunk (existing state)
        b: Second list of DocumentChunk (new updates)

    Returns:
        Merged list of DocumentChunk with combined properties
    """

    # Create a dictionary for quick lookup of chunks by index
    chunks_by_index = {chunk.chunk_index: chunk for chunk in a}

    # Merge updates from b into the existing chunks
    for updated_chunk in b:
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

            # Create the merged chunk
            chunks_by_index[updated_chunk.chunk_index] = DocumentChunk(**merged_data)

    # Return chunks in order by chunk_index
    return [chunks_by_index[i] for i in sorted(chunks_by_index.keys())]


class ClaimSubstantiationChunk(BaseModel):
    """
    Wrapper for a list of claim substantiation results for a single chunk.

    openapi-generator does not support List[List[T]] so we need to wrap the list of substantiations in a single model.
    """

    substantiations: List[ClaimSubstantiationResultWithClaimIndex]


class ClaimSubstantiatorState(BaseModel):
    # Inputs
    file: FileDocument
    supporting_files: Optional[List[FileDocument]] = None
    target_chunk_indices: Optional[List[int]] = None
    agents_to_run: Optional[List[str]] = None
    session_id: str = None

    # Outputs
    references: List[BibliographyItem] = []
    chunks: Annotated[List[DocumentChunk], conciliate_chunks] = []


class ChunkReevaluationRequest(BaseModel):
    """Request model for re-evaluating a specific chunk"""

    chunk_index: int = Field(
        ge=0, description="Zero-based index of the chunk to re-evaluate"
    )
    agents_to_run: List[str] = Field(
        description="List of agent types to run on the chunk",
        example=["claims", "citations"],
    )
    original_state: ClaimSubstantiatorState = Field(
        description="The original workflow state containing the document and chunks"
    )
    session_id: Optional[str] = Field(
        description="The session ID for Langfuse tracing"
    )


class ChunkReevaluationResponse(BaseModel):
    """Response model for chunk re-evaluation results"""

    chunk: DocumentChunk = Field(description="The re-evaluated chunk")

    agents_run: List[str] = Field(
        description="List of agents that were successfully run on the chunk"
    )
    processing_time_ms: Optional[float] = Field(
        description="Time taken to process the chunk in milliseconds", default=None
    )