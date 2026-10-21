"""E2E eval for the Review Assistant's revision-planning summary.

The Review Assistant runs the `review-assistant` skill over a reviewed draft
plus its reviewer memos and returns, for this output, one self-contained HTML
document: a Part 1 worklist for the author, and a Part 2 that reproduces every
memo verbatim with a planning note under each point.

The project is built the way an author would: the reviewed draft is the main
document, the memos are uploaded unlabeled, and a request for this one output
names them all. `peer_review_fixture` does that through the Review Assistant's
own endpoints.

The prose is free-form, so scoring splits in two:

Each scenario's draft and reviewer memos live as markdown under
`evals_inspectai/files/peer_review/<scenario>/`; the dataset references them and
carries the per-scenario expectations.

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

- `input_identification`, the share of documents the agent took for what
  they are: nobody labels them, so a misreading is what every other score
  would then inherit.

Each dataset sample plants a specific trap: conflicting reviewers, a compound
bullet that needs sub-point IDs, three reviewers on a commentary where many
asks are out of scope, a memo that refers to everything by a number the
revision will change, a memo dominated by trivial corrections, and a reviewer
who left only Word comments on a copy of the draft, which must count as a
reviewer of their own.
"""

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import Model, get_model
from inspect_ai.scorer import (
    Score,
    Scorer,
    Target,
    mean,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState

from evals_inspectai.common.docx_fixture import MarkedUpCopy
from evals_inspectai.common.loaders import resolve_input, yaml_dataset
from evals_inspectai.common.peer_review_fixture import (
    expected_input_roles,
    memo_document,
    review_assistant_solver,
)
from evals_inspectai.common.review_assistant_scorers import (
    STRUCTURE_CHECKS,
    extract_report,
    input_identification,
    report_structure,
)
from evals_inspectai.common.scorers import criteria_for, failed_score, grade_criteria
from evals_inspectai.common.viewer import checks_viewer_config

_TARGET_OUTPUT = "revision_planning_summary"

# Grader for the judged criteria. Set here rather than taking the shared
# `DEFAULT_GRADER_MODEL`, so changing this suite's judge does not silently
# re-grade the other eighteen e2e suites.
GRADER_MODEL = "openai/gpt-5.6-terra"

# The agent reads a whole draft plus every memo at high reasoning effort and
# writes a long HTML document, so it runs well past the default budget.
_WORKFLOW_TIMEOUT_S = 2400


def _record_to_sample(record: dict) -> Sample:
    """Build a sample from one dataset record.

    The draft and the reviewer memos are `file://` references, resolved here.
    Keeping them on disk as markdown rather than embedding them keeps the
    dataset readable and lets the fixture documents be edited as the documents
    they are. A memo may be given as a mapping instead, to add a `byline` (see
    `memo_document`), and a record may carry `marked_up` copies of the draft,
    built as Word files at upload time.
    """
    memos = [memo_document(entry) for entry in record.get("memos", [])]
    marked_up = [MarkedUpCopy.model_validate(m) for m in record.get("marked_up", [])]
    return Sample(
        id=record["id"],
        # The draft is the sample input so it reaches the grader as the question.
        input=resolve_input(record["draft"]),
        # The scenario's own criterion, shown as the sample target in the
        # viewer. The graded criteria are read from metadata, not from here.
        target=record["rubric"]["scenario_trap"],
        metadata={
            "output": _TARGET_OUTPUT,
            "memos": memos,
            "marked_up": [m.model_dump() for m in marked_up],
            "expected_roles": expected_input_roles(
                memo_names=[m["file_name"] for m in memos],
                marked_up_names=[m.file_name for m in marked_up],
            ),
            "expected_reviewers": record["expected_reviewers"],
            "point_count_bands": record["point_count_bands"],
            "verbatim_probes": record["verbatim_probes"],
            "rubric": record["rubric"],
        },
    )


def _load_dataset() -> MemoryDataset:
    return yaml_dataset(Path(__file__).parent / "dataset.yaml", _record_to_sample)


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


@scorer(metrics={name: [mean(), stderr()] for name in RUBRIC_CRITERIA})
def rubric_criteria(model: str | Model | None = None) -> Scorer:
    """Grade this suite's four criteria, each in its own grader call.

    The grader is shown the report's rendered text, not its HTML. Reading order
    and headings survive the flattening, which is what these criteria turn on,
    and the markup would otherwise be most of the prompt.
    """

    async def score(state: TaskState, target: Target) -> Score:
        report, reason = extract_report(state)
        if report is None:
            return failed_score(RUBRIC_CRITERIA, reason)

        return await grade_criteria(
            grader=get_model(model) if model else get_model(GRADER_MODEL),
            keys=RUBRIC_CRITERIA,
            criteria=criteria_for(state, SHARED_CRITERIA),
            answer=report.raw_text,
            question=state.input_text,
        )

    return score


SCORE_LABELS = {
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
    "input_identification": "Inputs",
}


@task
def revision_planning_summary_e2e():
    return Task(
        dataset=_load_dataset(),
        fail_on_error=0.2,
        solver=review_assistant_solver(timeout_s=_WORKFLOW_TIMEOUT_S),
        scorer=[
            report_structure(),
            rubric_criteria(),
            input_identification(),
        ],
        viewer=checks_viewer_config(
            [
                *(("report_structure", name) for name in STRUCTURE_CHECKS),
                *(("rubric_criteria", name) for name in RUBRIC_CRITERIA),
                ("input_identification", "input_identification"),
            ],
            SCORE_LABELS,
        ),
    )
