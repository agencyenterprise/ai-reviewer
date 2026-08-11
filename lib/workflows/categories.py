"""Workflow display configuration.

This module defines the single source of truth for:
- Which categories exist, their labels, and their display order
- Which workflows belong to each category and in what order within it

To reorder categories: change the order of entries in WORKFLOW_DISPLAY_CONFIG.
To reorder workflows within a category: change the order of the inner list.
"""

from typing import NamedTuple

from lib.workflows.models import WorkflowRunType


class CategoryConfig(NamedTuple):
    slug: str
    label: str
    workflows: list[WorkflowRunType]


WORKFLOW_DISPLAY_CONFIG: list[CategoryConfig] = [
    CategoryConfig(
        slug="citation_check",
        label="Citation Check",
        workflows=[
            # WorkflowRunType.REFERENCE_VALIDATION,  # legacy v1; kept registered so old projects still load.
            WorkflowRunType.REFERENCE_VALIDATION_V2,
        ],
    ),
    CategoryConfig(
        slug="substantive_review",
        label="Substantive Review",
        workflows=[
            # WorkflowRunType.CLAIM_REFERENCE_VALIDATION,
            WorkflowRunType.CLAIM_REFERENCE_VALIDATION_V2,
            WorkflowRunType.INFERENCE_VALIDATION_V2,
            WorkflowRunType.METHODOLOGICAL_ALIGNMENT,
            WorkflowRunType.RESULTS_EXTRACTION,
            WorkflowRunType.REVIEWER_2,
            WorkflowRunType.RECOMMENDATION_CHECK,
        ],
    ),
    CategoryConfig(
        slug="technical_compliance",
        label="Editorial and Style Review",
        workflows=[
            WorkflowRunType.ABBREVIATION_SCAN_V2,
            WorkflowRunType.ABOUT_THIS_GER,
            WorkflowRunType.DOCUMENT_STRUCTURE,
            WorkflowRunType.FIGURES_TABLES_CHECK,
        ],
    ),
    CategoryConfig(
        slug="language",
        label="Language",
        workflows=[
            # WorkflowRunType.ADVOCACY_TONE,  # legacy v1; kept registered so old projects still load.
            WorkflowRunType.ADVOCACY_TONE_V2,
        ],
    ),
    # The peer-review workflows (REVISION_PLANNING_SUMMARY,
    # REVIEWER_RESPONSE_MEMOS, REVIEWER_COVERAGE_REPORT) are deliberately absent.
    # They are started only from the Peer Review tab, which sequences their
    # prerequisites — memos first, then the revised draft — and starting them out
    # of order returns a guard message instead of a report. Leaving them out of
    # every category is what keeps them out of the assessment picker; they stay
    # registered, so existing runs still list and render normally.
    CategoryConfig(
        slug="research_writing_assistant",
        label="Research & Writing Assistant",
        workflows=[
            # WorkflowRunType.LITERATURE_REVIEW,  # legacy v1; kept registered so old projects still load.
            WorkflowRunType.LITERATURE_REVIEW_V2,
            # WorkflowRunType.CITATION_SUGGESTER,  # deprecated; superseded by Literature Review. Kept registered so old projects still load.
            # WorkflowRunType.LIVE_REPORTS,  # legacy v1; kept registered so old projects still load.
            WorkflowRunType.LIVE_REPORTS_V2,
        ],
    ),
]
