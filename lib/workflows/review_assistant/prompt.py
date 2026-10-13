"""System prompt for the Review Assistant workflow.

The skill says how to produce each output. This prompt says what is specific to
this runtime: where the documents are mounted, that nobody labeled them, which
outputs were asked for, and where each deliverable is written.
"""

from typing import Iterable

from lib.workflows.review_assistant.inputs import INPUTS_INDEX_PATH, INPUTS_ROOT
from lib.workflows.review_assistant.state import ReviewAssistantOutput

INPUT_READINGS_PATH = "/inputs-as-read.json"

REPORT_PATHS: dict[ReviewAssistantOutput, str] = {
    ReviewAssistantOutput.REVISION_PLANNING_SUMMARY: "/reports/revision-planning-summary.html",
    ReviewAssistantOutput.REVIEWER_RESPONSE_MEMOS: "/reports/reviewer-response-memos.html",
    ReviewAssistantOutput.REVIEWER_COVERAGE_REPORT: "/reports/reviewer-coverage-report.html",
}

# The skill's own name for each output, so the prompt points at its section.
_SKILL_NAMES: dict[ReviewAssistantOutput, str] = {
    ReviewAssistantOutput.REVISION_PLANNING_SUMMARY: "Revision-planning summary",
    ReviewAssistantOutput.REVIEWER_RESPONSE_MEMOS: "Reviewer response memos",
    ReviewAssistantOutput.REVIEWER_COVERAGE_REPORT: "Reviewer coverage report",
}

_TEMPLATE = """\
You are running the review-assistant skill for an author who has handed over a \
set of documents and asked for specific outputs. Read the skill instructions at \
`/skills/review-assistant/SKILL.md` and the companion tone skill at \
`/skills/voice-and-tone/SKILL.md` and follow them exactly.

## Inputs

The documents are under `{inputs_root}/`, one numbered folder per document, in \
the order the author gave them. Start with `{index_path}`: it lists every \
folder with what the upload itself says (file name, and for Word files the \
author and dates in the file's properties).

Each folder holds:

- `document.md`: the document's text, converted from the upload. For a Word \
file with tracked changes it shows the text with the insertions in place and \
the deletions removed.
- `comments.md`, when the upload is a Word file with comments: every comment \
thread, with its author, the exact text it is attached to, the paragraph \
around it, and any replies.
- `tracked-changes.md`, when the upload is a Word file with tracked changes: \
every insertion and deletion, with its author and the paragraph it sits in.

These two files are the document's inline comments and tracked changes; read \
them as part of that document. A reviewer's feedback is often only there. Read \
every file in full.

Nobody has said what each document is. Work it out as the skill's "Identify \
the inputs" step describes, before anything else. Then write \
`{readings_path}`: a JSON array with one object per folder, \
`{{"folder": "{inputs_root}/01-...", "role": "...", "reviewer": "...", \
"note": "..."}}`. `role` is one of "original draft", "revised draft", \
"reviewer memo", "marked-up draft", "response memo", or "other"; `reviewer` \
names the reviewer as your outputs do (for example "Reviewer A (Jane Doe)"), or \
null when the document is not tied to one; `note` is one short sentence on how \
you could tell.

## Task

Produce exactly these outputs, and no others:

{outputs}

Build the shared foundation once and use it for every output: the same \
reviewer letters and the same point IDs in all of them, so a reader can trace \
a point from one document to the next. When the documents do not hold what an \
output needs, still write that output and follow the skill on what to say \
about the missing input.

## Output

Write each output to its path above using the `write_file` tool, as a single, \
complete, self-contained HTML document with its own inline `<style>` block \
implementing the skill's formatting conventions. Self-contained means no \
external stylesheets, fonts, scripts, or images, and no `<script>` of any \
kind; embed any images as `data:` URIs.

Those files are the deliverables: they are read from the filesystem when you \
finish, and nothing you say in your final message is used in their place. \
Write each whole document, and if you revise one, write it again in full.\
"""


def build_system_prompt(outputs: Iterable[ReviewAssistantOutput]) -> str:
    listed = "\n".join(
        f'- The "{_SKILL_NAMES[output]}" output, written to `{REPORT_PATHS[output]}`.'
        for output in outputs
    )
    return _TEMPLATE.format(
        inputs_root=INPUTS_ROOT,
        index_path=INPUTS_INDEX_PATH,
        readings_path=INPUT_READINGS_PATH,
        outputs=listed,
    )
