"""Manifest for the Revision-Planning Summary workflow.

Runs the `review-assistant` skill against the original draft plus the uploaded
reviewer memos to produce a revision-planning summary: the reviewer memos
reproduced verbatim, each point labeled with a stable ID, and a compact planning
note under each point (where it lives in the draft, its scope, and a short
suggestion for addressing it).

This is the first of the three `review-assistant` outputs. The skill body
(`skills/review-assistant/SKILL.md`) is the single source of truth for how the
summary is produced; it is loaded as the agent's user prompt and is also mounted
read-only into the agent filesystem along with its voice-and-tone reference.
"""

from lib.models.file import FileRole
from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest

_SYSTEM_PROMPT = """\
You are running the review-assistant skill to produce a RAND revision-planning \
summary. Read the skill instructions at `/skills/review-assistant/SKILL.md` and \
its tone reference at `/skills/review-assistant/references/voice-and-tone.md` \
and follow them exactly.

## Inputs

- The original draft under review is at `/main.md`.
- The reviewer memos are at `/reviewer-memos/*.md` (one file per memo). Read \
every memo in full.

## Task

Produce ONLY the "Revision-planning summary" output described in the skill \
(not the reviewer response memos and not the coverage report). Reproduce each \
reviewer memo verbatim following the reviewer's own structure, label each point \
with its stable ID, and add a compact planning note under each point per the \
skill.

## Output

Write the complete revision-planning summary as Markdown into the \
`report_markdown` field of your structured response. Do NOT populate the \
`issues` field; this workflow produces a document deliverable, not a list of \
issues.

If there are no reviewer memos at `/reviewer-memos/`, do not invent content: set \
`report_markdown` to a short note stating that no reviewer memos were found and \
that one or more memos must be uploaded before a planning summary can be \
generated.\
"""


class RevisionPlanningSummaryManifest(SimpleDeepAgentManifest):
    """Generates a RAND revision-planning summary from reviewer memos."""

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
    file_roles = [FileRole.REVIEWER_MEMO]
