"""Manifest for the Revision-Planning Summary workflow.

Runs the `review-assistant` skill against the reviewed draft plus the uploaded
reviewer memos to produce a revision-planning summary: the reviewer memos
reproduced verbatim, each point labeled with a stable ID, and a compact planning
note under each point (where it lives in the draft, its scope, and a short
suggestion for addressing it).

This is the first of the three `review-assistant` outputs. The skill body
(`skills/review-assistant/SKILL.md`) is the single source of truth for how the
summary is produced; it is loaded as the agent's user prompt and is also mounted
read-only into the agent filesystem alongside the `voice-and-tone` skill.

It operates on the *reviewed revision*: the latest revision under `/revisions/`
that has reviewer memos attached. The agent finds it from the mounted file tree.
"""

from typing import TYPE_CHECKING, Optional

from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import HtmlReportDeepAgentManifest

if TYPE_CHECKING:
    from lib.services.file_artifacts_service.file_artifacts_service_type import (
        FileArtifactsServiceType,
    )

_SYSTEM_PROMPT = """\
You are running the review-assistant skill to produce a revision-planning \
summary. Read the skill instructions at `/skills/review-assistant/SKILL.md` and \
the companion tone skill at `/skills/voice-and-tone/SKILL.md` and follow them \
exactly.

## Inputs

The project's revisions are mounted under `/revisions/<n>/`. Find the \
**reviewed revision**: the highest-numbered revision folder that contains a \
`reviewer-memos/` directory. Ignore reviewer memos in any earlier revision.

- The draft under review is that revision's main document, \
`/revisions/<reviewed>/main.md`.
- The reviewer memos are the files under \
`/revisions/<reviewed>/reviewer-memos/`. Read every memo in full.

## Task

Produce ONLY the "Revision-planning summary" output described in the skill \
(not the reviewer response memos and not the coverage report). Reproduce each \
reviewer memo verbatim following the reviewer's own structure, label each point \
with its stable ID, and add a compact planning note under each point per the \
skill.

## Output

Produce a single, complete, self-contained HTML document for the revision-\
planning summary and write it into the `report_html` field of your structured \
response. Give it its own inline `<style>` block with a clean, readable report \
layout. The document must be fully self-contained: no external stylesheets, \
fonts, scripts, or images, and no `<script>` of any kind; embed any images as \
`data:` URIs.\
"""


class RevisionPlanningSummaryManifest(HtmlReportDeepAgentManifest):
    """Generates a revision-planning summary from reviewer memos."""

    type = WorkflowRunType.REVISION_PLANNING_SUMMARY
    name = "Revision-Planning Summary"
    description = (
        "Builds a revision-planning summary from reviewer notes/memos and the current "
        "draft. Produces a report that breaks every reviewer's points down into "
        "discrete, actionable suggestions and maps each to the part of the draft "
        "it corresponds to. Requires one or more reviewer memos."
    )
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]
    is_experimental = True

    skill = "review-assistant"
    system_prompt = _SYSTEM_PROMPT
    reasoning_effort = "high"

    async def precheck(self, service: "FileArtifactsServiceType") -> Optional[str]:
        if await service.get_latest_reviewer_memo_revision() is None:
            return (
                "No reviewer memos were found for this project. Upload one or "
                "more reviewer memos, then re-run this assessment."
            )
        return None
