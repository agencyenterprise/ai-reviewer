"""Tests for DOCX generation helper functions"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from lib.models.issue import Issue
from lib.services.docx.manipulator import CommentSeverity, DocxComment, issue_to_comment
from lib.workflows.models import DocumentIssue, SeverityEnum, WorkflowRunType

_FAKE_PROJECT_ID = uuid.uuid4()
_FAKE_WORKFLOW_RUN_ID = uuid.uuid4()


@dataclass
class _FakeChunk:
    chunk_index: int
    content: str
    start_line: int
    end_line: int


def _make_issue(
    title: str,
    description: str,
    severity: SeverityEnum,
    workflow_type: WorkflowRunType,
    chunk_indices: list[int] | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    long_description: str | None = None,
    suggested_action: str | None = None,
) -> Issue:
    """Create an Issue instance for testing without hitting the DB."""
    now = datetime.now(UTC)
    return Issue(
        id=uuid.uuid4(),
        project_id=_FAKE_PROJECT_ID,
        workflow_run_id=_FAKE_WORKFLOW_RUN_ID,
        issue_hash=uuid.uuid4().hex[:64],
        title=title,
        description=description,
        long_description=long_description,
        suggested_action=suggested_action,
        severity=severity,
        workflow_type=workflow_type,
        chunk_indices=chunk_indices,
        start_line=start_line,
        end_line=end_line,
        created_at=now,
        updated_at=now,
    )


class TestIssueToComment:
    """Tests for the issue_to_comment function"""

    def test_converts_issue_to_comment_successfully(self):
        issue = _make_issue(
            title="Unsupported Claim",
            description="This claim lacks evidence",
            severity=SeverityEnum.HIGH,
            workflow_type=WorkflowRunType.CLAIM_REFERENCE_VALIDATION,
            start_line=1,
            end_line=3,
        )
        chunks = [_FakeChunk(0, "The claim content here", 1, 3)]
        paragraph_line_ranges = {0: (1, 3)}

        comment = issue_to_comment(issue, chunks, paragraph_line_ranges)

        assert comment is not None
        assert isinstance(comment, DocxComment)
        assert comment.paragraph_index == 0
        assert "Unsupported Claim" in comment.comment_text
        assert "This claim lacks evidence" in comment.comment_text
        assert comment.severity == CommentSeverity.HIGH
        assert comment.get_author() == "🚨 High Priority"

    def test_includes_suggested_action_and_long_description_in_order(self):
        """Comment carries description, then suggested action, then long_description."""
        issue = _make_issue(
            title="Reference has incorrect fields",
            description="The publication year does not match public sources.",
            suggested_action="Update the year to 2021.",
            long_description="### Field validations\n\n- **Year**: 2019 → 2021",
            severity=SeverityEnum.HIGH,
            workflow_type=WorkflowRunType.REFERENCE_VALIDATION_V2,
            start_line=1,
            end_line=3,
        )
        chunks = [_FakeChunk(0, "The reference here", 1, 3)]
        paragraph_line_ranges = {0: (1, 3)}

        comment = issue_to_comment(issue, chunks, paragraph_line_ranges)

        assert comment is not None
        text = comment.comment_text
        assert "Suggested Action: Update the year to 2021." in text
        assert "### Field validations" in text
        assert "2019 → 2021" in text
        # Order: description → suggested action → long_description
        assert (
            text.index("does not match public sources")
            < text.index("Suggested Action:")
            < text.index("### Field validations")
        )

    def test_omits_long_description_when_absent(self):
        """No trailing separator/content when long_description is None."""
        issue = _make_issue(
            title="Unsupported Claim",
            description="This claim lacks evidence",
            severity=SeverityEnum.HIGH,
            workflow_type=WorkflowRunType.CLAIM_REFERENCE_VALIDATION,
            start_line=1,
            end_line=3,
        )
        chunks = [_FakeChunk(0, "The claim content here", 1, 3)]
        paragraph_line_ranges = {0: (1, 3)}

        comment = issue_to_comment(issue, chunks, paragraph_line_ranges)

        assert comment is not None
        assert comment.comment_text.endswith("This claim lacks evidence")

    def test_falls_back_to_chunk_indices_for_legacy_issue(self):
        """Issues pre-dating the line-range migration only carry chunk_indices."""
        issue = _make_issue(
            title="Legacy issue",
            description="Only has chunk_indices",
            severity=SeverityEnum.MEDIUM,
            workflow_type=WorkflowRunType.CLAIM_REFERENCE_VALIDATION,
            chunk_indices=[1],
        )
        chunks = [
            _FakeChunk(0, "Intro", 1, 2),
            _FakeChunk(1, "Body with the claim", 3, 5),
        ]
        paragraph_line_ranges = {0: (1, 2), 1: (3, 5)}

        comment = issue_to_comment(issue, chunks, paragraph_line_ranges)

        assert comment is not None
        assert comment.paragraph_index == 1

    def test_returns_none_when_line_range_unresolvable(self):
        issue = _make_issue(
            title="Invalid reference",
            description="Reference not found",
            severity=SeverityEnum.HIGH,
            workflow_type=WorkflowRunType.REFERENCE_VALIDATION,
        )
        chunks: list[_FakeChunk] = []

        comment = issue_to_comment(issue, chunks, {})

        assert comment is None

    def test_returns_none_when_no_paragraph_overlaps(self):
        issue = _make_issue(
            title="Some issue",
            description="Issue description",
            severity=SeverityEnum.MEDIUM,
            workflow_type=WorkflowRunType.CLAIM_REFERENCE_VALIDATION,
            start_line=100,
            end_line=110,
        )
        paragraph_line_ranges = {0: (1, 10), 1: (11, 20)}

        comment = issue_to_comment(issue, [], paragraph_line_ranges)

        assert comment is None

    def test_share_link_anchor_uses_line_range(self):
        issue = _make_issue(
            title="Some issue",
            description="Issue description",
            severity=SeverityEnum.HIGH,
            workflow_type=WorkflowRunType.CLAIM_REFERENCE_VALIDATION,
            start_line=5,
            end_line=15,
        )
        paragraph_line_ranges = {0: (1, 20)}

        comment = issue_to_comment(
            issue, [], paragraph_line_ranges, share_token="share-token-abc"
        )

        assert comment is not None
        assert comment.share_link is not None
        assert comment.share_link.endswith("#L5-15")

    def test_medium_severity_uses_correct_author(self):
        issue = _make_issue(
            title="Partially Supported",
            description="Some evidence found",
            severity=SeverityEnum.MEDIUM,
            workflow_type=WorkflowRunType.CLAIM_REFERENCE_VALIDATION,
            start_line=1,
            end_line=1,
        )
        paragraph_line_ranges = {0: (1, 1)}

        comment = issue_to_comment(issue, [], paragraph_line_ranges)

        assert comment.severity == CommentSeverity.MEDIUM
        assert comment.get_author() == "⚠️ Medium Priority"
        assert comment.get_initials() == "MP"

    def test_low_severity_uses_correct_author(self):
        issue = _make_issue(
            title="Minor Note",
            description="Just a suggestion",
            severity=SeverityEnum.LOW,
            workflow_type=WorkflowRunType.CITATION_SUGGESTER,
            start_line=1,
            end_line=1,
        )
        paragraph_line_ranges = {0: (1, 1)}

        comment = issue_to_comment(issue, [], paragraph_line_ranges)

        assert comment.severity == CommentSeverity.LOW
        assert comment.get_author() == "💡 Low Priority"
        assert comment.get_initials() == "LP"

