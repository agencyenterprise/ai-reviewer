from typing import List, TypedDict, Optional, Dict, Any
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


class ClaimSubstantiationChunk(BaseModel):
    """
    Wrapper for a list of claim substantiation results for a single chunk.

    openapi-generator does not support List[List[T]] so we need to wrap the list of substantiations in a single model.
    """

    substantiations: List[ClaimSubstantiationResultWithClaimIndex]


class ClaimSubstantiatorState(TypedDict, total=False):
    file: FileDocument
    supporting_files: List[FileDocument]

    # Selective processing controls (new)
    target_chunk_indices: Optional[List[int]]  # If None, process all chunks
    agents_to_run: Optional[List[str]]         # If None, run all agents

    # Outputs
    chunks: List[str]
    references: List[BibliographyItem]
    claims_by_chunk: List[ClaimResponse | ToulminClaimResponse]
    citations_by_chunk: List[CitationResponse]
    claim_substantiations_by_chunk: List[ClaimSubstantiationChunk]


class ChunkReevaluationRequest(BaseModel):
    """Request model for re-evaluating a specific chunk"""
    chunk_index: int = Field(
        ge=0, description="Zero-based index of the chunk to re-evaluate"
    )
    agents_to_run: List[str] = Field(
        description="List of agent types to run on the chunk",
        example=["claims", "citations"]
    )
    original_state: Dict[str, Any] = Field(
        description="The original workflow state containing the document and chunks"
    )


class ChunkReevaluationResponse(BaseModel):
    """Response model for chunk re-evaluation results"""
    chunk_index: int = Field(description="The index of the re-evaluated chunk")
    chunk_content: str = Field(description="The content of the re-evaluated chunk")
    claims_by_chunk: Optional[ClaimResponse | ToulminClaimResponse] = Field(
        description="Updated claims for this chunk", default=None
    )
    citations_by_chunk: Optional[CitationResponse] = Field(
        description="Updated citations for this chunk", default=None
    )
    claim_substantiations_by_chunk: Optional[ClaimSubstantiationChunk] = Field(
        description="Updated claim substantiations for this chunk", default=None
    )
    
    agents_run: List[str] = Field(
        description="List of agents that were successfully run on the chunk"
    )
    processing_time_ms: Optional[float] = Field(
        description="Time taken to process the chunk in milliseconds", default=None
    )
