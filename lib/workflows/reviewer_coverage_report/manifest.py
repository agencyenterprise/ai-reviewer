"""Manifest for the Reviewer Coverage Report workflow.

Runs the `review-assistant` skill to produce the QA-manager-facing coverage
report: a single consolidated view of every reviewer point, its verdict, and an
overall read on how responsive the revision was.

This is the third and final `review-assistant` output. Like the response memos,
it compares two revisions of the main document from the mounted file tree:

- the **original draft** = the main document of the *reviewed revision* (the
  latest revision under `/revisions/` with reviewer memos), and
- the **revised draft** = the current revision's main document at `/main.md`.

Coverage is assessed independently from the draft diff (an objective read for
the QAM); the author's response memos are not required.
"""

from typing import TYPE_CHECKING, Optional

from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import HtmlReportDeepAgentManifest

if TYPE_CHECKING:
    from lib.services.file_artifacts_service.file_artifacts_service_type import (
        FileArtifactsServiceType,
    )

_SYSTEM_PROMPT = """\
You are running the review-assistant skill to produce a reviewer coverage \
report for a QA manager. Read the skill instructions at \
`/skills/review-assistant/SKILL.md` and its tone reference at \
`/skills/review-assistant/references/voice-and-tone.md` and follow them exactly.

## Inputs

The project's revisions are mounted under `/revisions/<n>/`. Find the \
**reviewed revision**: the highest-numbered revision folder that contains a \
`reviewer-memos/` directory. Ignore reviewer memos in any earlier revision.

- The original draft (the version the reviewers reviewed) is \
`/revisions/<reviewed>/main.md`.
- The revised draft (the current version) is `/main.md`.
- The reviewer memos are the files under \
`/revisions/<reviewed>/reviewer-memos/`. Read every memo in full.

Assess coverage independently by comparing the revised draft against the \
original; you do not have the author's response memos.

## Task

Produce ONLY the "Reviewer coverage report" output described in the skill (not \
the revision-planning summary and not the reviewer response memos). Lay it out \
in the skill's order: (1) an opening with a title, the document type, the list \
of reviewers, and a short overall responsiveness read plus anything genuinely \
unaddressed; (2) a summary verdict table with per-category counts (addressed, \
partially addressed, declined with rationale, not addressed), totals and a \
per-reviewer breakdown, listing the point IDs in each category; (3) each \
reviewer's memo reproduced verbatim and in order, every point labeled with its \
stable ID, with the verdict, the point's location in the draft by content, and \
brief evidence directly under it. Be document-type aware, and note overlap \
between reviewers by point ID instead of double-counting.

## Output

Produce a single, complete, self-contained HTML document for the coverage \
report and write it into the `report_html` field of your structured response. \
Give it its own inline `<style>` block with a clean, readable layout — include \
a real styled table for the summary verdict counts and clearly distinguish each \
verdict. The document must be fully self-contained: no external stylesheets, \
fonts, scripts, or images, and no `<script>` of any kind; embed any images as \
`data:` URIs.\
"""


class ReviewerCoverageReportManifest(HtmlReportDeepAgentManifest):
    """Generates a consolidated reviewer coverage report for a QA manager."""

    type = WorkflowRunType.REVIEWER_COVERAGE_REPORT
    name = "Reviewer Coverage Report"
    description = (
        "Consolidates every reviewer's points into a single QA-manager view: a "
        "verdict per point (addressed, partially addressed, declined with "
        "rationale, or not addressed), a summary count table, and an overall "
        "responsiveness read. Requires reviewer memos and a revised draft "
        "(replace the main document after uploading the memos)."
    )
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]
    is_experimental = True

    skill = "review-assistant"
    system_prompt = _SYSTEM_PROMPT
    reasoning_effort = "high"

    async def precheck(self, service: "FileArtifactsServiceType") -> Optional[str]:
        reviewed_revision = await service.get_latest_reviewer_memo_revision()
        if reviewed_revision is None:
            return (
                "No reviewer memos were found for this project. Upload one or "
                "more reviewer memos, then re-run this assessment."
            )
        # The revised draft is the current main; it must differ from the
        # reviewed revision's main, otherwise there is nothing to assess.
        current_main = await service.get_main_file()
        original_main = await service.get_main_file(revision=reviewed_revision)
        if current_main.file_id == original_main.file_id:
            return (
                "The reviewed revision is still the current main document. "
                "Replace the main document with your revised draft, then re-run "
                "this assessment to generate a coverage report."
            )
        return None
