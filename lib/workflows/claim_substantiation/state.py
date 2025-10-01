from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
from operator import add

from lib.agents.citation_detector import CitationResponse
from lib.agents.citation_suggester import (
    CitationSuggestionResultWithClaimIndex,
)
from lib.agents.claim_common_knowledge_checker import (
    ClaimCommonKnowledgeResultWithClaimIndex,
)
from lib.agents.claim_detector import ClaimResponse
from lib.agents.literature_review import LiteratureReviewResponse
from lib.agents.toulmin_claim_detector import ToulminClaimResponse
from lib.agents.reference_extractor import BibliographyItem
from lib.agents.claim_substantiator import ClaimSubstantiationResultWithClaimIndex
from lib.services.file import FileDocument
from lib.agents.models import ChunkWithIndex
from lib.workflows.chunk_conciliator import create_conciliator
from lib.workflows.models import WorkflowError


class SubstantiationWorkflowConfig(BaseModel):
    """Configuration model for claim substantiation workflow"""

    use_toulmin: bool = Field(
        default=False, description="Whether to use Toulmin claim detection approach"
    )
    run_literature_review: bool = Field(
        default=False, description="Whether to run the literature review"
    )
    run_suggest_citations: bool = Field(
        default=False, description="Whether to run the citation suggestions"
    )
    target_chunk_indices: Optional[List[int]] = Field(
        default=None,
        description="Specific chunk indices to process (None = process all chunks)",
    )
    agents_to_run: Optional[List[str]] = Field(
        default=None, description="Specific agents to run (None = run all agents)"
    )
    domain: Optional[str] = Field(
        default=None, description="Domain context for more accurate analysis"
    )
    target_audience: Optional[str] = Field(
        default=None, description="Target audience context for analysis"
    )
    session_id: Optional[str] = Field(
        default=None, description="Session ID for Langfuse tracing"
    )


class DocumentChunk(ChunkWithIndex):
    """Independent chunk response object with all processing results"""

    claims: Optional[ClaimResponse | ToulminClaimResponse] = None
    citations: Optional[CitationResponse] = None
    claim_common_knowledge_results: List[ClaimCommonKnowledgeResultWithClaimIndex] = []
    substantiations: List[ClaimSubstantiationResultWithClaimIndex] = []
    citation_suggestions: List[CitationSuggestionResultWithClaimIndex] = []


class ClaimCommonKnowledgeResultChunk(BaseModel):
    """
    Wrapper for a list of claim common knowledge results for a single chunk.

    openapi-generator does not support List[List[T]] so we need to wrap the list of substantiations in a single model.
    """

    claim_common_knowledge_results: List[ClaimCommonKnowledgeResultWithClaimIndex]


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
    config: SubstantiationWorkflowConfig

    # Outputs
    references: List[BibliographyItem] = []
    chunks: Annotated[List[DocumentChunk], create_conciliator(DocumentChunk)] = []
    errors: Annotated[List[WorkflowError], add] = Field(
        default_factory=list,
        description="Errors that occurred during the processing of the document.",
    )
    literature_review: Optional[str] = None

    def get_paragraph_chunks(self, paragraph_index: int) -> List[DocumentChunk]:
        return [
            chunk for chunk in self.chunks if chunk.paragraph_index == paragraph_index
        ]

    def get_paragraph(self, paragraph_index: int) -> str:
        paragraph_chunks = self.get_paragraph_chunks(paragraph_index)
        return "\n".join([chunk.content for chunk in paragraph_chunks])


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
    session_id: Optional[str] = Field(description="The session ID for Langfuse tracing")


class ChunkReevaluationResponse(BaseModel):
    """Response model for chunk re-evaluation results"""

    state: ClaimSubstantiatorState = Field(
        description="The updated workflow state, with the re-evaluated chunk included"
    )
    agents_run: List[str] = Field(
        description="List of agents that were successfully run on the chunk"
    )
    processing_time_ms: Optional[float] = Field(
        description="Time taken to process the chunk in milliseconds", default=None
    )
