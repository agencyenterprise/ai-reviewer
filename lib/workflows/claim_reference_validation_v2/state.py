"""State, config, and reducer for Claim Reference Validation V2 workflow."""

from enum import Enum
from typing import Annotated, List, Literal, Optional

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field, field_serializer

from lib.agents.citation_validator import TruthfulnessLabel
from lib.agents.claim_verifier import ClaimEvidenceSource, EvidenceAlignmentLevel
from lib.workflows.models import BaseWorkflowConfig, BaseWorkflowState, WorkflowRunType


class CitationIssueItem(BaseModel):
    """Persisted workflow-state record for one validated citation.

    Built from the agent's `CitationAssessment` in the validate_section node.
    Unlike the agent output, this keeps the deprecated `evidence_alignment`
    field for backwards compatibility with workflow state persisted before the
    RAND taxonomy migration; new runs leave it unset and populate
    `truthfulness_label`.
    """

    quoted_text: str
    line_start: int
    line_end: int
    truthfulness_label: Optional[TruthfulnessLabel] = None
    # Deprecated: retained only so pre-migration persisted state still
    # deserializes. New runs never populate it.
    evidence_alignment: Optional[EvidenceAlignmentLevel] = None
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
