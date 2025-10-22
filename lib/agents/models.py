# lib/agents/enums.py
from enum import Enum
from langchain_core.documents import Document
from pydantic import BaseModel, Field, field_validator
from typing import Any


class DocumentMetadata(BaseModel):
    """Validated metadata for document chunks."""

    paragraph_index: int = Field(ge=0, description="Zero-based index of the paragraph")
    chunk_index: int = Field(ge=0, description="Zero-based global chunk index")
    chunk_index_within_paragraph: int = Field(
        ge=0, description="Zero-based index within the paragraph"
    )

    @field_validator("paragraph_index", "chunk_index", "chunk_index_within_paragraph")
    @classmethod
    def validate_indices(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Indices must be non-negative")
        return v


class ValidatedDocument(Document):
    """Document with validated metadata using Pydantic."""

    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)

    def __init__(self, page_content: str, **kwargs: Any) -> None:
        # Extract metadata from kwargs and validate it
        metadata_dict = kwargs.pop("metadata", {})

        # If metadata is provided as a dict, convert it to DocumentMetadata
        if isinstance(metadata_dict, dict):
            metadata = DocumentMetadata(**metadata_dict)
        elif isinstance(metadata_dict, DocumentMetadata):
            metadata = metadata_dict
        else:
            metadata = DocumentMetadata()

        super().__init__(page_content=page_content, metadata=metadata, **kwargs)


class ChunkWithIndex(BaseModel):
    content: str
    chunk_index: int
    paragraph_index: int


class ClaimCategory(str, Enum):
    ESTABLISHED = "established_reported_knowledge"
    METHODOLOGY = "methodology_procedural"
    RESULTS = "empirical_analytical_results"
    INTERPRETATION = "inferential_interpretive_claims"
    META = "meta_structural_evaluative"
    OTHER = "other"
