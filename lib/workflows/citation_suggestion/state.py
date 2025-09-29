from typing import Annotated, List, Optional
from pydantic import BaseModel, Field

from lib.agents.citation_detector import CitationResponse
from lib.agents.claim_detector import ClaimResponse
from lib.agents.toulmin_claim_detector import ToulminClaimResponse
from lib.agents.reference_extractor import BibliographyItem
from lib.agents.claim_substantiator import ClaimSubstantiationResultWithClaimIndex
from lib.services.file import FileDocument
from lib.agents.models import ChunkWithIndex
from lib.workflows.chunk_conciliator import create_conciliator
from operator import add

from lib.workflows.models import WorkflowError


class CitationSuggestionWorkflowConfig(BaseModel):
    """Configuration model for claim substantiation workflow"""

    # use_toulmin: bool = Field(
    #     default=False, description="Whether to use Toulmin claim detection approach"
    # )
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

    pass


class CitationSuggestionState(BaseModel):
    # Inputs
    file: FileDocument
    supporting_files: Optional[List[FileDocument]] = None
    # config: SubstantiationWorkflowConfig

    # Outputs
    references: List[BibliographyItem] = []
    chunks: Annotated[List[DocumentChunk], create_conciliator(DocumentChunk)] = []
    errors: Annotated[List[WorkflowError], add] = Field(
        default_factory=list,
        description="Errors that occurred during the processing of the document.",
    )

    def get_paragraph_chunks(self, paragraph_index: int) -> List[DocumentChunk]:
        return [
            chunk for chunk in self.chunks if chunk.paragraph_index == paragraph_index
        ]

    def get_paragraph(self, paragraph_index: int) -> str:
        paragraph_chunks = self.get_paragraph_chunks(paragraph_index)
        return "\n".join([chunk.content for chunk in paragraph_chunks])
