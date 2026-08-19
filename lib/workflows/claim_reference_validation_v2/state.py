"""State, config, and reducer for Claim Reference Validation V2 workflow."""

from enum import Enum
from typing import Annotated, List, Literal, Optional

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field, field_serializer

from lib.agents.citation_validator import TruthfulnessLabel
from lib.agents.claim_verifier import ClaimEvidenceSource, EvidenceAlignmentLevel
from lib.workflows.models import (
    BaseWorkflowConfig,
    BaseWorkflowState,
    ErrorDetails,
    WorkflowRunType,
)


class CitationIssueItem(BaseModel):
    """Persisted workflow-state record for one validated citation.

    Built from the agent's `CitationAssessment` in the validate_section node.
    New runs populate `evidence_alignment` (supported / partially_supported /
    unsupported / unverifiable). The deprecated 6-category `truthfulness_label`
    is retained only so workflow state persisted before the migration back to
    `EvidenceAlignmentLevel` still deserializes; the manifest maps it onto the
    new taxonomy for rendering.
    """

    quoted_text: str
    line_start: int
    line_end: int
    evidence_alignment: Optional[EvidenceAlignmentLevel] = None
    # Deprecated: retained only so pre-migration persisted state still
    # deserializes. New runs never populate it.
    truthfulness_label: Optional[TruthfulnessLabel] = None
    rationale: str = ""
    feedback: str = ""
    evidence_sources: List[ClaimEvidenceSource] = Field(default_factory=list)
    citation_to_file_mapping: Optional[str] = None


class ClaimReferenceValidationV2Config(BaseWorkflowConfig):
    type: Literal[WorkflowRunType.CLAIM_REFERENCE_VALIDATION_V2] = Field(
        WorkflowRunType.CLAIM_REFERENCE_VALIDATION_V2
    )


class SectionVerificationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    # The model's response was cut off mid-output; the assessments it had
    # finished were salvaged, so the section carries both issues and an error.
    PARTIAL = "partial"
    ERROR = "error"
    CANCELLED = "cancelled"


class SectionVerificationItem(BaseModel):
    section_index: int
    start_line: int = 1
    end_line: int = 1
    headings: List[str] = Field(default_factory=list)
    status: SectionVerificationStatus = SectionVerificationStatus.PENDING
    num_citations: int = 0
    issues: List[CitationIssueItem] = Field(default_factory=list)
    error: Optional[str] = None
    error_details: Optional[ErrorDetails] = Field(
        default=None,
        description="Traceback, raw model output, and LLM metadata for a failed section.",
    )
    messages: List[BaseMessage] = Field(
        default_factory=list,
        description="LLM conversation messages from the citation-validator agent invocation.",
    )

    @field_serializer("messages")
    @classmethod
    def _serialize_messages(cls, messages: List[BaseMessage]) -> list[dict]:
        # Checkpointer-hydrated states may contain raw dicts in `messages`
        # because reducers can append items that bypass model construction.
        return [m if isinstance(m, dict) else m.model_dump() for m in messages]


def merge_section_verifications(
    existing: List[SectionVerificationItem],
    new: List[SectionVerificationItem],
) -> List[SectionVerificationItem]:
    """Reducer: merge by section_index, allowing PENDING → COMPLETED/ERROR transitions."""
    by_index = {item.section_index: item for item in existing}
    for item in new:
        by_index[item.section_index] = item
    return list(by_index.values())


class ClaimReferenceValidationV2State(BaseWorkflowState):
    type: Literal[WorkflowRunType.CLAIM_REFERENCE_VALIDATION_V2] = Field(
        WorkflowRunType.CLAIM_REFERENCE_VALIDATION_V2
    )
    config: ClaimReferenceValidationV2Config

    section_verifications: Annotated[
        List[SectionVerificationItem], merge_section_verifications
    ] = Field(default_factory=list)

    citation_issues: List[CitationIssueItem] = Field(default_factory=list)
