"""Scoring shared by the `review-assistant` e2e suites.

The Review Assistant's outputs (revision-planning summary, reviewer response
memos, reviewer coverage report) are each one self-contained HTML document
built from the same skill, so a large part of what makes an output
correct is identical across them: the reviewer memos reproduced verbatim inside
marked quotes, a valid per-reviewer point-ID scheme numbered from 1 with no
gaps, a self-contained document (no external stylesheets, fonts, scripts or
images, and no `<script>`), a two-part layout with a short first part, and none
of the generic-assistant tells the `voice-and-tone` skill bans, counted only
outside quotes so the reviewer's own punctuation is not held against it.

`report_structure` scores exactly those rules and belongs to every suite, as
does `input_identification`: the documents arrive unlabeled, and the agent
records what it took each one to be. Each suite then adds whatever its own
output specifies on top -- the coverage report has a verdict table to check,
the planning summary does not.

The judged criteria differ per suite, so none of them live here. The machinery
that runs them -- `grade_criteria`, `criteria_for` -- and the per-check scoring
helpers -- `checks_to_score`, `failed_score` -- are generic and live in
`common.scorers`, which any suite can use.

Scorers here report a dict of values so every check is its own Inspect metric.
That constrains the callers: Inspect raises when a declared metric key is
missing from any sample's score, so every code path has to return the full key
set, which is what `failed_score` is for.
"""

import json
from itertools import permutations
from typing import Any

from inspect_ai.scorer import Score, Scorer, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState
from pydantic import BaseModel, Field, ValidationError

from evals_inspectai.common.html_report import (
    HtmlReport,
    find_point_ids,
    self_containment_violations,
    top_level_ids_by_reviewer,
    two_part_layout,
    voice_tells,
)
from evals_inspectai.common.scorers import checks_to_score, failed_score

# Below this, the report is too short to be a real deliverable regardless of
# what else it gets right.
MIN_REPORT_CHARS = 2000

# One key per rule the skill states outright. Reported as separate metrics
# rather than averaged into one number, so a regression names itself in the
# results table instead of showing up as a fractional dip to read out of an
# explanation string.
STRUCTURE_CHECKS = (
    "verbatim",
    "quoted",
    "id_scheme",
    "self_contained",
    "two_part_layout",
    "voice",
)


class ReviewAssistantReport(BaseModel):
    """Local mirror of one report in the Review Assistant's state."""

    output: str
    report_html: str = ""


class ReviewAssistantInput(BaseModel):
    """Local mirror of one mounted document: its file and its folder."""

    file_name: str
    folder: str


class ReviewAssistantInputReading(BaseModel):
    """Local mirror of what the agent took one document to be."""

    folder: str
    role: str = ""


class ReviewAssistantOutput(BaseModel):
    """Local mirror of ReviewAssistantState, as far as the scorers read it.

    One run carries a report per requested output under ``reports``, the
    documents it mounted under ``inputs``, and what the agent took each one to
    be under ``input_readings``; the rest (``config``, ``messages``) is ignored.
    """

    reports: list[ReviewAssistantReport] = Field(default_factory=list)
    inputs: list[ReviewAssistantInput] = Field(default_factory=list)
    input_readings: list[ReviewAssistantInputReading] = Field(default_factory=list)


def parse_output(state: TaskState) -> ReviewAssistantOutput:
    """The run's state, or an empty one when it cannot be read."""
    try:
        return ReviewAssistantOutput.model_validate(
            json.loads(state.output.completion or "{}")
        )
    except (ValueError, ValidationError):
        return ReviewAssistantOutput()


def reports_by_output(state: TaskState) -> dict[str, HtmlReport]:
    """Every substantive report the run wrote, by output."""
    return {
        r.output: HtmlReport(r.report_html)
        for r in parse_output(state).reports
        if len(r.report_html) >= MIN_REPORT_CHARS
    }


def _normalize_role(role: str) -> str:
    return " ".join(role.lower().replace("-", " ").split())


def identification_checks(
    output: ReviewAssistantOutput, expected_roles: dict[str, str]
) -> tuple[float, list[str]]:
    """The share of documents read as their expected role, and a line per document."""
    folders = {i.file_name: i.folder for i in output.inputs}
    readings = {r.folder.rstrip("/"): r for r in output.input_readings}
    lines: list[str] = []
    correct = 0
    for file_name, role in expected_roles.items():
        reading = readings.get(folders.get(file_name, ""))
        got = _normalize_role(reading.role) if reading else ""
        ok = got == _normalize_role(role)
        correct += ok
        lines.append(
            f"{'PASS' if ok else 'FAIL'} {file_name}: expected {role!r}, read as {got or 'nothing'!r}"
        )
    return (correct / len(expected_roles) if expected_roles else 0.0), lines


@scorer(metrics=[mean(), stderr()])
def input_identification() -> Scorer:
    """The share of documents the agent took for what they are.

    Read from the notes the agent leaves on how it read the inputs, against the
    sample's ``expected_roles``: nobody tells it which document is which, so a
    wrong reading is the failure every output then inherits.
    """

    async def score(state: TaskState, target: Target) -> Score:
        expected: dict[str, str] = (state.metadata or {})["expected_roles"]
        value, lines = identification_checks(parse_output(state), expected)
        return Score(value=value, explanation="\n".join(lines))

    return score


def extract_report(state: TaskState) -> tuple[HtmlReport | None, str]:
    """Parse the workflow state into the sample's report, or explain why it cannot be.

    The report is the one for the output the sample asked for, named by its
    ``output`` metadata. Returns `(report, "")` on success and `(None, reason)`
    otherwise, so every scorer rejects an unusable output the same way and for
    the same reasons.
    """
    wanted = (state.metadata or {}).get("output")
    try:
        output = ReviewAssistantOutput.model_validate_json(state.output.completion)
    except ValidationError as e:
        return None, f"Could not parse the workflow state: {e}"

    html = next((r.report_html for r in output.reports if r.output == wanted), "")
    if len(html) < MIN_REPORT_CHARS:
        return None, f"No substantive HTML report for {wanted!r} ({len(html)} chars)"
    return HtmlReport(html), ""


def check_id_scheme(
    grouped: dict[str, set[int]], meta: dict[str, Any]
) -> tuple[bool, str]:
    """Validate reviewer letters, per-reviewer point counts, and numbering gaps.

    Which memo gets which letter is not checked. The agent sees the documents
    as `/inputs/NN-<slug>/document.md` in the order the request names them,
    and the skill letters reviewers in the order their documents are given,
    but nobody tells it which documents are memos: it works that out, and a
    marked-up copy or an unexpected reading can shift a letter without anything
    being wrong. The bands are therefore satisfied by any assignment of
    expected counts to the letters actually used, which still catches a
    dropped or merged reviewer.
    """
    expected: list[str] = meta["expected_reviewers"]
    bands: dict[str, list[int]] = meta["point_count_bands"]

    problems: list[str] = []

    used = sorted(grouped)
    if used != sorted(expected):
        problems.append(
            f"reviewer letters {used or 'none'}, expected {sorted(expected)}"
        )
    else:
        counts = [len(grouped[letter]) for letter in used]
        band_list = [tuple(bands[letter]) for letter in expected]
        if not any(
            all(low <= count <= high for count, (low, high) in zip(counts, order))
            for order in permutations(band_list)
        ):
            problems.append(
                f"per-reviewer point counts {counts} fit no assignment of the "
                f"expected bands {band_list}"
            )

    for letter, numbers in sorted(grouped.items()):
        if numbers and sorted(numbers) != list(range(1, max(numbers) + 1)):
            missing = sorted(set(range(1, max(numbers) + 1)) - numbers)
            problems.append(f"{letter} numbering has gaps at {missing}")

    summary = ", ".join(f"{k}={len(v)}" for k, v in sorted(grouped.items()))
    return (
        not problems,
        f"points per reviewer: {summary or 'none'}"
        + ("; " + "; ".join(problems) if problems else ""),
    )


def structure_checks(
    report: HtmlReport, meta: dict[str, Any]
) -> dict[str, tuple[bool, str]]:
    """Run the six rules, returning (passed, detail) per check."""
    checks: dict[str, tuple[bool, str]] = {}

    # Every memo is reproduced verbatim. The probes are distinctive sentences
    # drawn from across each memo, including its trailing sections, since
    # dropping the tail is the likely failure.
    probes: list[str] = meta["verbatim_probes"]
    missing = [p for p in probes if not report.contains(p)]
    checks["verbatim"] = (
        not missing,
        f"{len(probes) - len(missing)}/{len(probes)} memo probes reproduced"
        + (f"; first missing: {missing[0][:60]!r}" if missing else ""),
    )

    # Reviewer text is marked as a quote, so the boundary between the
    # reviewer's words and the workflow's own is unmistakable.
    unquoted = [p for p in probes if report.contains(p) and not report.quotes(p)]
    checks["quoted"] = (
        not unquoted,
        (
            "reviewer text is inside marked quotes"
            if not unquoted
            else f"{len(unquoted)} reproduced probe(s) sit outside any quote"
        ),
    )

    # One letter per reviewer, numbered from 1 with no gaps, and a plausible
    # number of points per reviewer.
    grouped = top_level_ids_by_reviewer(find_point_ids(report.raw_text))
    checks["id_scheme"] = check_id_scheme(grouped, meta)

    # A self-contained document, as all three system prompts require.
    violations = self_containment_violations(report.html)
    checks["self_contained"] = (
        not violations,
        "self-contained" if not violations else "; ".join(violations),
    )

    # A visible two-part split with a short first part, keyed on the page break
    # rather than on heading wording.
    checks["two_part_layout"] = two_part_layout(report)

    # Voice tells, counted only outside quotes: the memo is reproduced
    # verbatim, so the reviewer's own punctuation is not held against it.
    tells = voice_tells(report.raw_unquoted_text)
    checks["voice"] = (
        not any(tells.values()),
        (
            "no generic-AI tells in own prose"
            if not any(tells.values())
            else ", ".join(f"{k}={v}" for k, v in tells.items() if v)
        ),
    )
    return checks


@scorer(metrics={name: [mean(), stderr()] for name in STRUCTURE_CHECKS})
def report_structure() -> Scorer:
    """Score the skill's exactly-checkable rules, one metric per rule.

    A single scorer returning a dict rather than six separate scorers: the
    checks share the HTML parse, which is the expensive part, and Inspect
    reports each key as its own metric either way. That is the documented
    split -- separate scorers when they are genuinely independent, one
    dict-valued scorer when they share computation.
    """

    async def score(state: TaskState, target: Target) -> Score:
        report, reason = extract_report(state)
        if report is None:
            return failed_score(STRUCTURE_CHECKS, reason)
        return checks_to_score(structure_checks(report, state.metadata or {}))

    return score


def revision_question(state: TaskState) -> str:
    """Both drafts, and any response memos, labelled, as the question put to a grader.

    For the outputs that compare a revision with what the reviewers asked.
    Passing only the reviewed draft made those criteria unjudgeable and
    actively wrong: the grader compared the output's claims about what changed
    against the draft that had *not* changed, concluded the revisions were
    fabricated, and marked accurate replies and verdicts as incorrect.
    """
    meta = state.metadata or {}
    question = (
        "There are two versions of the document. The reviewer memos were "
        "written against the first; the second is the author's revision "
        "answering them.\n\n"
        "=== REVIEWED DRAFT (what the reviewers saw) ===\n"
        f"{state.input_text}\n\n"
        "=== REVISED DRAFT (what the author changed it to) ===\n"
        f"{meta.get('revised_draft', '')}\n"
    )
    # The replies are claims the output is meant to check, so the grader needs
    # them to tell a verified claim from one taken on trust.
    for memo in meta.get("response_memos", []):
        question += (
            f"\n=== AUTHOR RESPONSE MEMO: {memo['file_name']} "
            "(the author's replies; claims, not evidence) ===\n"
            f"{memo['content']}\n"
        )
    return question
