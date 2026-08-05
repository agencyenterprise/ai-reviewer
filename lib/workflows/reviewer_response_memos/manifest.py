"""Manifest for the Reviewer Response Memos workflow.

Runs the `review-assistant` skill to produce one response memo per reviewer:
each reviewer point echoed verbatim with the author's reply stating how the
revision addressed it (or why it was not changed).

This is the second of the three `review-assistant` outputs. It compares two
revisions of the main document, both available in the mounted file tree:

- the **original draft** = the main document of the *reviewed revision* (the
  latest revision under `/revisions/` with reviewer memos), and
- the **revised draft** = the current revision's main document at `/main.md`.

The revised draft is supplied through the ordinary revision flow ("Replace main
document"); there is no separate upload for it.
"""

from typing import TYPE_CHECKING, Optional

from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import HtmlReportDeepAgentManifest

if TYPE_CHECKING:
    from lib.services.file_artifacts_service.file_artifacts_service_type import (
        FileArtifactsServiceType,
    )

_SYSTEM_PROMPT = """\
You are running the review-assistant skill to produce reviewer response memos. \
Read the skill instructions at `/skills/review-assistant/SKILL.md` and its tone \
reference at `/skills/review-assistant/references/voice-and-tone.md` and follow \
them exactly.

## Inputs

The project's revisions are mounted under `/revisions/<n>/`. Find the \
**reviewed revision**: the highest-numbered revision folder that contains a \
`reviewer-memos/` directory. Ignore reviewer memos in any earlier revision.

- The original draft (the version the reviewers reviewed) is \
`/revisions/<reviewed>/main.md`.
- The revised draft (the current version that addresses the comments) is \
`/main.md`.
- The reviewer memos are the files under \
`/revisions/<reviewed>/reviewer-memos/`. Read every memo in full.

## Task

Produce ONLY the "Reviewer response memos" output described in the skill (not \
the revision-planning summary and not the coverage report): one response memo \
per reviewer. For every reviewer point, echo the reviewer's text verbatim, then \
compare the revised draft against the original to determine what actually \
changed and write the author's reply accordingly (addressed and where, \
partially addressed, or not changed with a reason).

## Output

Produce a single, complete, self-contained HTML document containing all the \
response memos and write it into the `report_html` field of your structured \
response. Give it its own inline `<style>` block with a clean, readable layout \
that clearly distinguishes each reviewer's verbatim text from the author's \
reply. The document must be fully self-contained: no external stylesheets, \
fonts, scripts, or images, and no `<script>` of any kind; embed any images as \
`data:` URIs.\
"""


class ReviewerResponseMemosManifest(HtmlReportDeepAgentManifest):
    """Generates one reviewer response memo per reviewer, comparing revisions."""

    type = WorkflowRunType.REVIEWER_RESPONSE_MEMOS
    name = "Reviewer Response Memos"
    description = (
        "Drafts one response memo per reviewer, comparing the revised draft (the "
        "current main document) against the reviewed draft. Each reviewer point "
        "is echoed verbatim with a reply on how the revision addressed it. "
        "Requires reviewer memos and a revised draft (replace the main document "
        "after uploading the memos)."
    )
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]
    is_experimental = True

    skill = "review-assistant"
    system_prompt = _SYSTEM_PROMPT

    async def precheck(self, service: "FileArtifactsServiceType") -> Optional[str]:
        reviewed_revision = await service.get_latest_reviewer_memo_revision()
        if reviewed_revision is None:
            return (
                "No reviewer memos were found for this project. Upload one or "
                "more reviewer memos, then re-run this assessment."
            )
        # The revised draft is the current main; it must differ from the
        # reviewed revision's main, otherwise there is nothing to compare.
        current_main = await service.get_main_file()
        original_main = await service.get_main_file(revision=reviewed_revision)
        if current_main.file_id == original_main.file_id:
            return (
                "The reviewed revision is still the current main document. "
                "Replace the main document with your revised draft, then re-run "
                "this assessment to generate response memos."
            )
        return None
