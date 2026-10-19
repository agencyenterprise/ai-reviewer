"""State definitions for document summarization workflow."""

from typing import Annotated, Literal

from pydantic import Field

from lib.agents.document_summarizer import DocumentSummary
from lib.workflows.models import BaseWorkflowConfig, BaseWorkflowState, WorkflowRunType
from lib.workflows.reducers import Reducer, upsert_by


class DocumentSummarizationWorkflowConfig(BaseWorkflowConfig):
    """Configuration model for document summarization workflow."""

    type: Literal[WorkflowRunType.DOCUMENT_SUMMARIZATION] = Field(
        WorkflowRunType.DOCUMENT_SUMMARIZATION
    )


class FileSummary(DocumentSummary):
    """Summary of a file. Extends DocumentSummary to include the file ID to match the summary to the file."""

    file_id: str = Field(description="The ID of the file")


# Upserts by file_id so each parallel summarization replaces that file's summary.
merge_summaries: Reducer[FileSummary] = upsert_by(lambda s: s.file_id)


class DocumentSummarizationState(BaseWorkflowState):
    """State for document summarization workflow."""

    type: Literal[WorkflowRunType.DOCUMENT_SUMMARIZATION] = Field(
        WorkflowRunType.DOCUMENT_SUMMARIZATION
    )

    # Inputs
    config: DocumentSummarizationWorkflowConfig
    main_file_id: str = Field(
        description="ID of the main document to summarize (full content used)",
    )
    supporting_file_ids: list[str] = Field(
        default_factory=list,
        description="IDs of supporting documents to summarize (truncated content used)",
    )

    # Outputs
    summaries: Annotated[list[FileSummary], merge_summaries] = Field(
        default_factory=list,
        description="List of document summaries for main and supporting files",
    )
