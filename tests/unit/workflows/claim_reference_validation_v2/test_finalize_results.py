"""Tests for how finalize_results treats partially-validated sections.

A PARTIAL section is one whose model response was cut off after some
assessments completed. It has to contribute both — its salvaged issues and the
error explaining what was lost — so the run neither drops recovered work nor
reports a clean bill of health.
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
    assert "recovered 1 assessment(s)" in error.error
    assert error.details is not None
    assert error.details.error_type == "PartialSectionValidationError"


@pytest.mark.asyncio
async def test_partial_section_reports_a_warning_so_the_run_stays_completed():
    """A salvaged section must not collapse the whole run to 'failed' in the UI."""
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

    assert result["errors"][0].severity == WorkflowErrorSeverity.WARNING


@pytest.mark.asyncio
async def test_failed_section_reports_a_blocking_error():
    result = await _finalize(
        _state(_section(8, SectionVerificationStatus.ERROR, error="hard failure"))
    )

    assert result["errors"][0].severity == WorkflowErrorSeverity.ERROR


@pytest.mark.asyncio
async def test_failed_section_contributes_an_error_and_no_issues():
    result = await _finalize(
        _state(_section(8, SectionVerificationStatus.ERROR, error="hard failure"))
    )

    assert result["citation_issues"] == []
    assert len(result["errors"]) == 1


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
