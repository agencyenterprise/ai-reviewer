"""Tests for how finalize_results reports section-level failures.

A failed or partially-validated section costs part of the document, not the
run, so it is reported as a warning and the run still reads as completed. The
exception is a run where nothing completed: with no issues to show, a warning
would let an empty result set render as an all-clear.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from lib.workflows.claim_reference_validation_v2.nodes.validate_sections import (
    finalize_results,
)
from lib.workflows.claim_reference_validation_v2.state import (
    CitationIssueItem,
    ClaimReferenceValidationV2Config,
    ClaimReferenceValidationV2State,
    SectionVerificationItem,
    SectionVerificationStatus,
)
from lib.workflows.models import ErrorDetails, WorkflowErrorSeverity, WorkflowRunType

RUN_ID = "e19f91af-9be6-45d2-8d7c-a05285b7bda0"


def _issue(quoted_text: str) -> CitationIssueItem:
    return CitationIssueItem(quoted_text=quoted_text, line_start=1, line_end=1)


def _section(
    index: int,
    status: SectionVerificationStatus,
    issues: list[CitationIssueItem] | None = None,
    error: str | None = None,
) -> SectionVerificationItem:
    return SectionVerificationItem(
        section_index=index,
        start_line=107,
        end_line=125,
        headings=["The Idea of a CERN for AI"],
        status=status,
        issues=issues or [],
        num_citations=len(issues or []),
        error=error,
        error_details=ErrorDetails(error_type="PartialSectionValidationError")
        if error
        else None,
    )


def _state(*sections: SectionVerificationItem) -> ClaimReferenceValidationV2State:
    return ClaimReferenceValidationV2State(
        type=WorkflowRunType.CLAIM_REFERENCE_VALIDATION_V2,
        config=ClaimReferenceValidationV2Config(
            type=WorkflowRunType.CLAIM_REFERENCE_VALIDATION_V2,
            project_id="project-1",
        ),
        section_verifications=list(sections),
    )


async def _finalize(state: ClaimReferenceValidationV2State) -> dict:
    # Call the node body directly: the register_node wrapper only adds progress
    # tracking, which needs a database.
    runtime = SimpleNamespace(context=SimpleNamespace(workflow_run_id=RUN_ID))
    return await finalize_results.__wrapped__(state, runtime)


@pytest.mark.asyncio
async def test_partial_section_contributes_its_salvaged_issues():
    result = await _finalize(
        _state(
            _section(0, SectionVerificationStatus.COMPLETED, [_issue("done")]),
            _section(
                8,
                SectionVerificationStatus.PARTIAL,
                [_issue("salvaged")],
                error="truncated; recovered 1 assessment(s)",
            ),
        )
    )

    assert [i.quoted_text for i in result["citation_issues"]] == ["done", "salvaged"]


@pytest.mark.asyncio
async def test_partial_section_still_reports_an_error():
    result = await _finalize(
        _state(
            _section(
                8,
                SectionVerificationStatus.PARTIAL,
                [_issue("salvaged")],
                error="truncated; recovered 1 assessment(s)",
            ),
        )
    )

    assert len(result["errors"]) == 1
    error = result["errors"][0]
    assert error.task_name == "validate_section"
    assert error.workflow_run_id == RUN_ID
    assert error.details is not None
    assert error.details.error_type == "PartialSectionValidationError"


@pytest.mark.asyncio
async def test_partial_section_message_names_what_was_lost():
    result = await _finalize(
        _state(
            _section(0, SectionVerificationStatus.COMPLETED, [_issue("done")]),
            _section(
                8,
                SectionVerificationStatus.PARTIAL,
                [_issue("salvaged")],
                error="truncated; recovered 1 assessment(s)",
            ),
        )
    )

    message = result["errors"][0].error
    assert "Section 8" in message
    assert "lines 107-125" in message
    assert "1 citation assessment(s) were recovered" in message


@pytest.mark.asyncio
async def test_failed_section_message_names_the_section_and_the_cause():
    """The reader needs to know a whole section is missing, and why."""
    result = await _finalize(
        _state(
            _section(0, SectionVerificationStatus.COMPLETED, [_issue("done")]),
            _section(10, SectionVerificationStatus.ERROR, error="hard failure"),
        )
    )

    message = result["errors"][0].error
    assert "Section 10 (The Idea of a CERN for AI, lines 107-125)" in message
    assert "citations are missing from these results" in message
    assert "hard failure" in message


@pytest.mark.asyncio
async def test_section_failures_are_warnings_while_other_sections_produced_results():
    """31 good sections out of 33 is not a failed run."""
    result = await _finalize(
        _state(
            _section(0, SectionVerificationStatus.COMPLETED, [_issue("done")]),
            _section(
                8,
                SectionVerificationStatus.PARTIAL,
                [_issue("salvaged")],
                error="truncated",
            ),
            _section(10, SectionVerificationStatus.ERROR, error="hard failure"),
        )
    )

    assert [e.severity for e in result["errors"]] == [
        WorkflowErrorSeverity.WARNING,
        WorkflowErrorSeverity.WARNING,
    ]


@pytest.mark.asyncio
async def test_a_partial_section_alone_still_counts_as_results():
    result = await _finalize(
        _state(
            _section(
                8,
                SectionVerificationStatus.PARTIAL,
                [_issue("salvaged")],
                error="truncated",
            ),
        )
    )

    assert result["errors"][0].severity == WorkflowErrorSeverity.WARNING


@pytest.mark.asyncio
async def test_every_section_failing_escalates_to_a_blocking_error():
    """With nothing to show, a warning would let an empty run look all-clear."""
    result = await _finalize(
        _state(
            _section(8, SectionVerificationStatus.ERROR, error="hard failure"),
            _section(10, SectionVerificationStatus.ERROR, error="hard failure"),
        )
    )

    assert result["citation_issues"] == []
    assert [e.severity for e in result["errors"]] == [
        WorkflowErrorSeverity.ERROR,
        WorkflowErrorSeverity.ERROR,
    ]


@pytest.mark.asyncio
async def test_completed_and_cancelled_sections_report_no_errors():
    result = await _finalize(
        _state(
            _section(0, SectionVerificationStatus.COMPLETED, [_issue("done")]),
            _section(1, SectionVerificationStatus.CANCELLED),
            _section(2, SectionVerificationStatus.PENDING),
        )
    )

    assert [i.quoted_text for i in result["citation_issues"]] == ["done"]
    assert result["errors"] == []
