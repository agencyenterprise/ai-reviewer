"""Scoring shared by the `review-assistant` e2e suites.

The three review-assistant workflows (revision-planning summary, reviewer
response memos, reviewer coverage report) all deliver one self-contained HTML
document built from the same skill, so a large part of what makes an output
correct is identical across them: the reviewer memos reproduced verbatim inside
marked quotes, a valid point-ID scheme, a self-contained document, a two-part
layout with a short first part, and none of the generic-assistant tells the
`voice-and-tone` skill bans.

`report_structure` scores exactly those rules and belongs to every suite. Each
suite then adds whatever its own output specifies on top -- the coverage report
has a verdict table to check, the planning summary does not.

The judged criteria differ per suite, so only their machinery lives here:
`grade_criteria` runs one grader call per criterion concurrently. What the
criteria *are* is each suite's business.

Both scorers report a dict of values so every check is its own Inspect metric.
That constrains the callers: Inspect raises when a declared metric key is
missing from any sample's score, so every code path has to return the full key
set, which is what `failed_score` is for.
"""

import asyncio
import re
from itertools import permutations
from typing import Any, Sequence

from inspect_ai.model import Model
from inspect_ai.scorer import Score, Scorer, Target, mean, scorer, stderr
from inspect_ai.scorer._model import (  # type: ignore[attr-defined]
    DEFAULT_GRADE_PATTERN,
    DEFAULT_MODEL_GRADED_FACT_TEMPLATE,
    default_instructions,
)
from inspect_ai.solver import TaskState
from pydantic import ValidationError

from evals_inspectai.common.html_report import (
    HtmlReport,
    find_point_ids,
    self_containment_violations,
    top_level_ids_by_reviewer,
    two_part_layout,
    voice_tells,
)
from evals_inspectai.common.simple_deep_agent_types import HtmlReportAgentOutput

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


def failed_score(keys: Sequence[str], reason: str) -> Score:
    """Score every key as failed, for an output there is nothing to check in."""
    return Score(value={key: 0.0 for key in keys}, explanation=reason)


def extract_report(state: TaskState) -> tuple[HtmlReport | None, str]:
    """Parse the workflow state into a report, or explain why it cannot be.

    Returns `(report, "")` on success and `(None, reason)` otherwise, so both
    scorers reject an unusable output the same way and for the same reasons.
    """
    try:
        output = HtmlReportAgentOutput.model_validate_json(state.output.completion)
    except ValidationError as e:
        return None, f"Could not parse the workflow state: {e}"

    html = (output.result.report_html if output.result else "") or ""
    if len(html) < MIN_REPORT_CHARS:
        return None, f"No substantive HTML report ({len(html)} chars)"
    return HtmlReport(html), ""


def check_id_scheme(
    grouped: dict[str, set[int]], meta: dict[str, Any]
) -> tuple[bool, str]:
    """Validate reviewer letters, per-reviewer point counts, and numbering gaps.

    Which memo gets which letter is not checked. The skill letters reviewers in
    the order their memos are provided, but the agent sees the memos as
    `/revisions/<n>/reviewer-memos/<file_id>.md`, so the mounted tree carries
    neither the original file names nor a stable order. Holding the eval to a
    specific assignment would score a coin flip. The bands are therefore
    satisfied by any assignment of expected counts to the letters actually
    used, which still catches a dropped or merged reviewer.
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


def checks_to_score(checks: dict[str, tuple[bool, str]]) -> Score:
    """Turn per-check results into a dict-valued Score."""
    return Score(
        value={name: float(ok) for name, (ok, _) in checks.items()},
        explanation=" | ".join(
            f"{'PASS' if ok else 'FAIL'} {name}: {detail}"
            for name, (ok, detail) in checks.items()
        ),
    )


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


# --- Judged criteria -------------------------------------------------------

# C / P / I as the grader returns them.
GRADE_VALUES = {"C": 1.0, "P": 0.5, "I": 0.0}


def criteria_for(state: TaskState, shared: dict[str, str]) -> dict[str, str]:
    """Shared criteria, with any per-sample text from the dataset layered on."""
    overrides = (state.metadata or {}).get("rubric") or {}
    return {**shared, **overrides}


async def _grade_one(
    grader: Model, criterion: str, answer: str, question: str
) -> tuple[float, str]:
    """Grade a single criterion, returning its value and the grader's reasoning."""
    prompt = DEFAULT_MODEL_GRADED_FACT_TEMPLATE.format(
        question=question,
        answer=answer,
        criterion=criterion,
        instructions=default_instructions(partial_credit=True),
    )
    result = await grader.generate(prompt)
    match = re.search(DEFAULT_GRADE_PATTERN, result.completion)
    if not match:
        return 0.0, f"grade not found in grader output: {result.completion[:300]}"
    return GRADE_VALUES.get(match.group(1), 0.0), result.completion


async def grade_criteria(
    grader: Model,
    keys: Sequence[str],
    criteria: dict[str, str],
    answer: str,
    question: str,
) -> Score:
    """Grade each criterion in its own call, concurrently, into one Score.

    One grader call per criterion rather than one call weighing all of them.
    Judging them together lets a single weak area colour the rest, which is the
    behaviour that made a single blended grade hard to act on. The calls run
    concurrently, so the extra cost is tokens rather than wall clock.
    """
    graded = await asyncio.gather(
        *(_grade_one(grader, criteria[key], answer, question) for key in keys)
    )
    return Score(
        value={key: value for key, (value, _) in zip(keys, graded)},
        explanation="\n\n".join(
            f"### {key}: {value}\n{reasoning}"
            for key, (value, reasoning) in zip(keys, graded)
        ),
    )
