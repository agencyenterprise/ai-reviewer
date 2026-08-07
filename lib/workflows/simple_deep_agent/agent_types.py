"""Shared types for simple deep-agent workflows.

Defines the canonical IssueItem and AgentCheckResult models used by all
single-node deep-agent workflows, plus the helper that converts them into
DocumentIssue objects.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from lib.workflows.models import DocumentIssue, SeverityEnum, WorkflowRunType


class IssueItem(BaseModel):
    """Lightweight issue returned by a deep agent."""

    title: str = Field(description="Short issue title")
    description: str = Field(
        description="Detailed description of the issue. Supports markdown."
    )
    severity: Literal["none", "low", "medium", "high"] = Field(
        default="medium",
        description="Issue severity: none, low, medium, or high. Use 'none' for informational items that should be surfaced but do not represent a problem.",
    )
    long_description: Optional[str] = Field(
        default=None,
        description=(
            "Extended markdown description for issues that require more detail than fits in "
            "description. Use markdown headings, lists, and code blocks to improve readability. "
            "Leave unset when description alone is sufficient."
        ),
    )
    suggested_action: Optional[str] = Field(
        default=None,
        description=(
            "A direct, concise recommendation to the author on what to do to resolve this "
            "issue. Markdown is supported."
        ),
    )
    start_line: int = Field(
        description="1-indexed start line in the document where the text relevant to this issue begins",
    )
    end_line: int = Field(
        description="1-indexed end line in the document where the text relevant to this issue ends",
    )


# --- LLM structured-output models ---------------------------------------
# Each deep-agent variant forces one of these as the model's response schema,
# so the LLM sees only the fields it should populate. They are mapped into the
# unified DeepAgentResult that the workflow state stores.


class AgentCheckResult(BaseModel):
    """LLM output for a validation pass: issues plus a markdown report."""

    issues: List[IssueItem] = Field(
        default_factory=list,
        description="Issues found during validation",
    )
    report_markdown: str = Field(
        default="",
        description="Markdown report summarising the check results",
    )


class AgentHtmlReport(BaseModel):
    """LLM output for a pass that produces an HTML report deliverable."""

    issues: List[IssueItem] = Field(
        default_factory=list,
        description="Optional issues found while producing the report",
    )
    report_html: str = Field(
        default="",
        description=(
            "A complete, self-contained HTML document for the report: its own "
            "inline <style>, no external resources (fonts/images/scripts), and "
            "images only as data: URIs."
        ),
    )


# --- Unified state result ------------------------------------------------


class DeepAgentResult(BaseModel):
    """Unified result stored in the workflow state.

    Holds the superset of what the deep-agent variants produce. Exactly one
    report field is populated per run (markdown workflows fill
    ``report_markdown``; HTML workflows fill ``report_html``); the UI renders
    whichever is present. ``issues`` is populated by the markdown variant only.
    """

    issues: List[IssueItem] = Field(default_factory=list)
    report_markdown: str = Field(default="")
    report_html: str = Field(default="")


_SEVERITY_MAP = {
    "none": SeverityEnum.NONE,
    "low": SeverityEnum.LOW,
    "medium": SeverityEnum.MEDIUM,
    "high": SeverityEnum.HIGH,
}


def issues_from_agent_result(
    result: AgentCheckResult | DeepAgentResult,
    workflow_type: WorkflowRunType,
) -> List[DocumentIssue]:
    """Convert a result's issues into DocumentIssue objects.

    Emits line ranges only; ``chunk_indices`` is left unset and derived at
    persistence time from the line range.
    """

    return [
        DocumentIssue(
            title=issue.title,
            type=workflow_type,
            description=issue.description,
            long_description=issue.long_description,
            suggested_action=issue.suggested_action,
            severity=_SEVERITY_MAP.get(issue.severity.lower(), SeverityEnum.MEDIUM),
            start_line=issue.start_line,
            end_line=issue.end_line,
        )
        for issue in result.issues
    ]
