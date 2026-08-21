"""E2E eval for the revision_planning_summary workflow.

The workflow runs the `review-assistant` skill over a reviewed draft plus its
reviewer memos and returns one self-contained HTML document: a Part 1 worklist
for the author, and a Part 2 that reproduces every memo verbatim with a
planning note under each point.

Unlike the other e2e evals, the project this needs cannot be created by a
single upload: the memos have to carry the `reviewer_memo` role, which only the
TUS path can set, and the workflow short-circuits through its precheck if they
are missing. `peer_review_fixture` builds that project and then starts the
workflow against it.

The prose is free-form, so scoring splits in two:

- `report_structure`, for the rules the skill states outright and that can be
  checked exactly. It reports one metric per rule (memos reproduced verbatim,
  reviewer text inside marked quotes, a valid and gap-free point-ID scheme, a
  self-contained document, a two-part layout with a short first part, and no
  generic-AI voice tells in the workflow's own prose), so a regression names
  itself in the results table rather than averaging away.
- `rubric_criteria`, for the judgement the skill asks for that no rule can
  capture. It grades four criteria independently, each reported as its own
  metric: locating points by content rather than by a number that will move,
  triaging Part 1 into substantial asks versus a count of quick fixes, carrying
  a scope and a suggestion under every point, and the trap the scenario plants.

Each dataset sample plants a specific trap: conflicting reviewers, a compound
bullet that needs sub-point IDs, three reviewers on a commentary where many
asks are out of scope, a memo that refers to everything by a number the
revision will change, and a memo dominated by trivial corrections.
"""

import asyncio
import json
import re
from itertools import permutations
from pathlib import Path
from typing import Any

import yaml
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import Model, ModelOutput, get_model
from inspect_ai.scorer import (
    Score,
    Scorer,
    Target,
    mean,
    scorer,
    stderr,
)
from inspect_ai.scorer._model import (  # type: ignore[attr-defined]
    DEFAULT_GRADE_PATTERN,
    DEFAULT_MODEL_GRADED_FACT_TEMPLATE,
    default_instructions,
)
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.viewer import (
    SampleScoreView,
    ScoreColorScale,
    SampleScoreViewSort,
    TaskSamplesColumn,
    TaskSamplesSort,
    TaskSamplesView,
    ViewerConfig,
)
from langchain_core.messages.utils import convert_to_messages
from pydantic import ValidationError

from evals_inspectai.common.converters import messages_from_langchain
from evals_inspectai.common.html_report import (
    HtmlReport,
    find_point_ids,
    self_containment_violations,
    top_level_ids_by_reviewer,
    two_part_layout,
    voice_tells,
)
from evals_inspectai.common.loaders import resolve_input
from evals_inspectai.common.peer_review_fixture import (
    ReviewerMemo,
    run_review_assistant_workflow,
    setup_peer_review_project,
)
from evals_inspectai.common.simple_deep_agent_types import HtmlReportAgentOutput

_TARGET_WORKFLOW = "revision_planning_summary"

# Grader for the judged criteria. Set here rather than taking the shared
# `DEFAULT_GRADER_MODEL`, so changing this suite's judge does not silently
# re-grade the other eighteen e2e suites.
GRADER_MODEL = "openai/gpt-5.6-terra"

# The agent reads a whole draft plus every memo at high reasoning effort and
# writes a long HTML document, so it runs well past the default budget.
_WORKFLOW_TIMEOUT_S = 2400

# Below this, the report is too short to be a real deliverable regardless of
# what else it gets right.
_MIN_REPORT_CHARS = 2000


def _record_to_sample(record: dict) -> Sample:
    """Build a sample from one dataset record.

    Memos are embedded in the dataset as literal YAML blocks, next to the
    verbatim probes that are checked against them, so their line breaks and
    indentation survive exactly as a reviewer would have written them. The
    draft is a `file://` reference: it is bulk input that nothing is matched
    against character by character.
    """
    return Sample(
        id=record["id"],
        # The draft is the sample input so it reaches the grader as the question.
        input=resolve_input(record["draft"]),
        # The scenario's own criterion, shown as the sample target in the
        # viewer. The graded criteria are read from metadata, not from here.
        target=record["rubric"]["scenario_trap"],
        metadata={
            "memos": record["memos"],
            "expected_reviewers": record["expected_reviewers"],
            "point_count_bands": record["point_count_bands"],
            "verbatim_probes": record["verbatim_probes"],
            "rubric": record["rubric"],
        },
    )


def _load_dataset() -> MemoryDataset:
    """Read the YAML dataset into memory.

    Inspect ships CSV and JSON loaders but not YAML, so the records are read
    here and handed over as a `MemoryDataset`. YAML is worth that small amount
    of glue: the memos are multi-paragraph documents with meaningful line
    breaks, bullet indentation, and blank lines, and a literal block keeps them
    legible and diffable in a way a JSON string with escaped newlines does not.
    """
    path = Path(__file__).parent / "dataset.yaml"
    records = yaml.safe_load(path.read_text())
    return MemoryDataset(
        samples=[_record_to_sample(record) for record in records],
        name="revision_planning_summary",
        location=str(path),
    )


@solver
def revision_planning_summary_solver(
    timeout_s: float = _WORKFLOW_TIMEOUT_S,
    poll_interval_s: float = 10,
) -> Solver:
    """Build a peer-review project from the sample, then run the workflow on it.

    A custom solver rather than the shared `api_workflow_agent` because the
    project needs reviewer memos in place before the workflow starts; see
    `peer_review_fixture`.
    """

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata or {}

        project_id = await setup_peer_review_project(
            draft=state.input_text,
            memos=[
                ReviewerMemo(file_name=m["file_name"], content=m["content"])
                for m in meta["memos"]
            ],
        )

        run_detail = await run_review_assistant_workflow(
            project_id=project_id,
            workflow_type=_TARGET_WORKFLOW,
            timeout_s=timeout_s,
            poll_interval_s=poll_interval_s,
        )

        workflow_state = run_detail.get("state") or {}

        # Hand the agent's own conversation to Inspect so the log viewer shows
        # the transcript, the same way the shared `api_workflow_agent` does.
        # They are lifted out of the state dict rather than copied, so the
        # completion the scorers parse stays just the workflow result.
        raw_messages = workflow_state.pop("messages", [])
        if raw_messages:
            state.messages = messages_from_langchain(convert_to_messages(raw_messages))

        state.output = ModelOutput(
            completion=json.dumps(workflow_state),
            model="api",
        )
        return state

    return solve


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


def _all_failed(reason: str) -> Score:
    """Score every check as failed, for outputs there is nothing to check."""
    return Score(
        value={name: 0.0 for name in STRUCTURE_CHECKS},
        explanation=reason,
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
        try:
            output = HtmlReportAgentOutput.model_validate_json(state.output.completion)
        except ValidationError as e:
            return _all_failed(f"Could not parse the workflow state: {e}")

        html = (output.result.report_html if output.result else "") or ""
        if len(html) < _MIN_REPORT_CHARS:
            return _all_failed(f"No substantive HTML report ({len(html)} chars)")

        report = HtmlReport(html)
        meta = state.metadata or {}
        checks: dict[str, tuple[bool, str]] = {}

        # Every memo is reproduced verbatim. The probes are distinctive
        # sentences drawn from across each memo, including its trailing
        # sections, since dropping the tail is the likely failure.
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

        # One letter per reviewer, numbered from 1 with no gaps, and a
        # plausible number of points per reviewer.
        grouped = top_level_ids_by_reviewer(find_point_ids(report.raw_text))
        checks["id_scheme"] = _check_id_scheme(grouped, meta)

        # A self-contained document, as all three system prompts require.
        violations = self_containment_violations(html)
        checks["self_contained"] = (
            not violations,
            "self-contained" if not violations else "; ".join(violations),
        )

        # A visible two-part split with a short first part, keyed on the page
        # break rather than on heading wording.
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

        return Score(
            value={name: float(ok) for name, (ok, _) in checks.items()},
            explanation=" | ".join(
                f"{'PASS' if ok else 'FAIL'} {name}: {detail}"
                for name, (ok, detail) in checks.items()
            ),
        )

    return score


def _check_id_scheme(
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


# The rubric, decomposed. One prose brief per sample produced a single grade
# that said "something was weak" without saying which judgement, and let one
# poor area drag the rest. Each criterion is now graded on its own and reported
# as its own metric.
#
# The key set has to be identical across every sample: Inspect raises when a
# declared metric key is missing from any sample's score. So a criterion that
# only applies to one scenario lives inside `scenario_trap`, whose text varies
# per sample, rather than becoming a key of its own.
RUBRIC_CRITERIA = (
    "locations_by_content",
    "part1_triage",
    "planning_notes",
    "scenario_trap",
)

# Criteria that hold for every sample. A dataset record may override any of
# these; in practice only `scenario_trap` is set per sample.
SHARED_CRITERIA: dict[str, str] = {
    "locations_by_content": (
        "Every reviewer point is located by what it is about rather than by a number that "
        "will move. Descriptions such as 'the section introducing the five concepts' or "
        "'the concept about overnight minima' satisfy this. Locations given as 'Concept 4', "
        "'Section 3' or 'page 8' do not, because the author's revision renumbers and retitles "
        "sections. Reviewer memos habitually refer to places by number, so carrying those "
        "numbers over as the location is the specific failure to look for."
    ),
    "part1_triage": (
        "Part 1 is the author's worklist, not a retelling of the memos. It separates the "
        "substantial asks, which need real work, from the quick fixes, which are trivial "
        "corrections. Each substantial ask gets one line with its point ID. The quick fixes "
        "are reduced to a count with their IDs listed and are not spelled out individually. "
        "Filing a substantial ask among the quick fixes, or spelling trivia out in Part 1, "
        "both fail this."
    ),
    "planning_notes": (
        "Under each quoted reviewer point in Part 2 there is a compact planning note carrying "
        "three things: the point's scope (document-wide, section-level, or paragraph-level), "
        "where it lives in the draft, and a one or two sentence suggestion for addressing it. "
        "A point reproduced without a planning note, or a note missing the scope or the "
        "suggestion, fails this."
    ),
}

# C / P / I as the grader returns them.
_GRADE_VALUES = {"C": 1.0, "P": 0.5, "I": 0.0}


def _criteria_for(state: TaskState) -> dict[str, str]:
    """Shared criteria, with any per-sample text layered on top."""
    overrides = (state.metadata or {}).get("rubric") or {}
    return {**SHARED_CRITERIA, **overrides}


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
    return _GRADE_VALUES.get(match.group(1), 0.0), result.completion


@scorer(metrics={name: [mean(), stderr()] for name in RUBRIC_CRITERIA})
def rubric_criteria(model: str | Model | None = None) -> Scorer:
    """Grade each rubric criterion independently.

    One grader call per criterion rather than one call weighing all of them.
    Judging them together lets a single weak area colour the rest, which is the
    behaviour that made the old single grade hard to act on. The calls run
    concurrently, so the extra cost is tokens rather than wall clock.

    The grader is shown the report's rendered text, not its HTML. Reading order
    and headings survive the flattening, which is what these criteria turn on,
    and the markup would otherwise be most of the prompt.
    """

    async def score(state: TaskState, target: Target) -> Score:
        try:
            output = HtmlReportAgentOutput.model_validate_json(state.output.completion)
        except ValidationError as e:
            return Score(
                value={name: 0.0 for name in RUBRIC_CRITERIA},
                explanation=f"Could not parse the workflow state: {e}",
            )

        html = (output.result.report_html if output.result else "") or ""
        if len(html) < _MIN_REPORT_CHARS:
            return Score(
                value={name: 0.0 for name in RUBRIC_CRITERIA},
                explanation=f"No substantive HTML report ({len(html)} chars)",
            )

        answer = HtmlReport(html).raw_text
        criteria = _criteria_for(state)
        grader = get_model(model) if model else get_model(GRADER_MODEL)

        graded = await asyncio.gather(
            *(
                _grade_one(grader, criteria[name], answer, state.input_text)
                for name in RUBRIC_CRITERIA
            )
        )

        return Score(
            value={name: value for name, (value, _) in zip(RUBRIC_CRITERIA, graded)},
            explanation="\n\n".join(
                f"### {name}: {value}\n{reasoning}"
                for name, (value, reasoning) in zip(RUBRIC_CRITERIA, graded)
            ),
        )

    return score


def _viewer_config() -> ViewerConfig:
    """Log-viewer defaults tuned to how this eval is actually read.

    Two questions come up every run: which check regressed, and whether the
    workflow is stable across epochs. The grid is arranged to answer both at a
    glance, and the long text fields are hidden because they would otherwise
    dominate every row -- the input is a whole draft and the target is a
    paragraph of criterion prose, neither of which is scannable in a table.

    These are defaults, not overrides: they apply until a reviewer customises
    the view in their own browser.
    """
    score_columns = [
        *(
            TaskSamplesColumn.score("report_structure", name)
            for name in STRUCTURE_CHECKS
        ),
        *(TaskSamplesColumn.score("rubric_criteria", name) for name in RUBRIC_CRITERIA),
    ]

    return ViewerConfig(
        task_samples_view=TaskSamplesView(
            name="Checks and epochs",
            columns=[
                TaskSamplesColumn(id="sampleStatus"),
                # Which fixture, and which of its runs. Both matter here: each
                # sample plants a different trap, and the epochs are the
                # determinism read.
                TaskSamplesColumn(id="sampleId"),
                TaskSamplesColumn(id="epoch"),
                *score_columns,
                # The structured-output parse failure surfaces here, and it is
                # frequent enough to be worth a permanent column.
                TaskSamplesColumn(id="error"),
                TaskSamplesColumn(id="duration"),
                # Hidden: the draft and the criterion text are far too long to
                # scan, and token counts cover only the graders, not the
                # workflow.
                TaskSamplesColumn(id="input", visible=False),
                TaskSamplesColumn(id="target", visible=False),
                TaskSamplesColumn(id="answer", visible=False),
                TaskSamplesColumn(id="tokens", visible=False),
            ],
            # Group each sample's epochs together rather than floating failures
            # to the top: comparing epochs of one fixture is the main reading,
            # and the colour scales already make a weak cell obvious.
            sort=[
                TaskSamplesSort(column="sampleId", dir="asc"),
                TaskSamplesSort(column="epoch", dir="asc"),
            ],
            # Ten score columns; rotate the headers and keep rows compact.
            compact_scores=True,
            multiline=False,
            # Full check names do not fit a narrow column.
            score_labels={
                "verbatim": "Verbatim",
                "quoted": "Quoted",
                "id_scheme": "IDs",
                "self_contained": "Self-cont.",
                "two_part_layout": "Layout",
                "voice": "Voice",
                "locations_by_content": "Locations",
                "part1_triage": "Triage",
                "planning_notes": "Notes",
                "scenario_trap": "Trap",
            },
            # Everything is numeric with 1 good. The rubric criteria are no
            # longer categorical C/P/I: they are graded that way and mapped to
            # 1.0 / 0.5 / 0.0 before scoring, so a partial reads as a mid tone
            # rather than needing its own colour role.
            # Every score here is numeric on a fixed 0-to-1 domain, so pin the
            # domain rather than leaving it to the viewer's default, which
            # anchors each palette to that column's *observed* range. Two
            # things go wrong with the default. A check that passes on every
            # run has min == max, no range to map, and paints nothing, so the
            # healthy columns look unevaluated. And an identical score reads
            # differently per column: 0.5 was the floor of `part1_triage`
            # (observed 0.5-1.0) and painted as bad, while the same 0.5 was
            # the midpoint of `scenario_trap` (observed 0.0-1.0) and painted as
            # middling. Pinning 0..1 makes a cell's colour mean the same thing
            # in every column and gives a passing column its full-marks green.
            score_color_scales={
                name: ScoreColorScale(palette="good-high", min=0.0, max=1.0)
                for name in (*STRUCTURE_CHECKS, *RUBRIC_CRITERIA)
            },
            color_scales_enabled=True,
        ),
        sample_score_view=SampleScoreView(
            default="chips",
            sort=SampleScoreViewSort(column="value", dir="asc"),
        ),
    )


@task
def revision_planning_summary_e2e():
    return Task(
        dataset=_load_dataset(),
        fail_on_error=0.2,
        solver=revision_planning_summary_solver(),
        scorer=[
            report_structure(),
            rubric_criteria(),
        ],
        viewer=_viewer_config(),
    )
