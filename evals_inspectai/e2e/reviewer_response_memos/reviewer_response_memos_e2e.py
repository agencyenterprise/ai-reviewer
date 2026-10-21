"""E2E eval for the Review Assistant's reviewer response memos.

The Review Assistant runs the `review-assistant` skill over a reviewed draft, the
revised draft that answers the memos, and the reviewer memos, and returns, for
this output, one self-contained HTML document holding a response memo per
reviewer: each memo echoes every reviewer point verbatim and replies, as the
author, with what changed and where or why it did not. Points the revision does
not answer and gives no reason for go in a block at the top for the author,
marked to be removed before sending, instead of getting an invented reply.

The scenarios are the coverage report's (see its dataset), so what each revision
did is known; the traps say what the replies have to get right about it. The
documents are uploaded unlabeled and named in one request (see
`peer_review_fixture`), and one sample asks for all three outputs at once, the
way an author wanting the whole round would.

Scoring:

- `memo_structure`: the shared rules from `review_assistant_scorers` except the
  two-part layout, which the skill exempts the response memos from, plus
  `flags_block`, the internal block at the top. In this flow the block is always
  there: when the agent identified the documents itself, the skill puts the list
  of how it read them in that block, which then appears even without flags.
- `request_outputs`: every requested output came back, and the reviewer letters
  and point IDs are the same across them. Only the all-outputs sample has more
  than one output to compare; a single output passes `ids_consistent` as there
  is nothing to disagree with.
- `rubric_criteria`: four judged criteria, each graded in its own call, with
  both drafts shown to the grader.
- `input_identification`: the share of documents the agent took for what they are.
"""

import re
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import Model, get_model
from inspect_ai.scorer import Score, Scorer, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState

from evals_inspectai.common.html_report import (
    HtmlReport,
    find_point_ids,
    top_level_ids_by_reviewer,
)
from evals_inspectai.common.loaders import resolve_input, yaml_dataset
from evals_inspectai.common.peer_review_fixture import (
    expected_input_roles,
    memo_document,
    review_assistant_solver,
)
from evals_inspectai.common.review_assistant_scorers import (
    extract_report,
    input_identification,
    reports_by_output,
    revision_question,
    structure_checks,
)
from evals_inspectai.common.scorers import (
    checks_to_score,
    criteria_for,
    failed_score,
    grade_criteria,
)
from evals_inspectai.common.viewer import checks_viewer_config

_TARGET_OUTPUT = "reviewer_response_memos"

# Grader for the judged criteria, set per suite rather than shared, so changing
# this suite's judge does not silently re-grade any other.
GRADER_MODEL = "openai/gpt-5.6-terra"

# Two full drafts plus every memo at high reasoning effort; the all-outputs
# sample writes three long documents from one run.
_WORKFLOW_TIMEOUT_S = 3600

# The shared rules that apply to this output, and the one it adds.
MEMO_CHECKS = (
    "verbatim",
    "quoted",
    "id_scheme",
    "self_contained",
    "voice",
    "flags_block",
)
REQUEST_CHECKS = ("outputs_delivered", "ids_consistent")

# How the skill tells the author to delete the block before the memo goes out.
_BEFORE_SENDING = re.compile(
    r"\b(before (sending|you send|it is sent|this is sent|the memos? (is|are) sent))\b",
    re.IGNORECASE,
)


def _record_to_sample(record: dict) -> Sample:
    """Build a sample: the reviewed draft as input, the rest in metadata."""
    memos = [memo_document(ref) for ref in record["memos"]]
    return Sample(
        id=record["id"],
        input=resolve_input(record["draft"]),
        target=record["rubric"]["scenario_trap"],
        metadata={
            "output": _TARGET_OUTPUT,
            "outputs": record.get("outputs", [_TARGET_OUTPUT]),
            "memos": memos,
            "revised_draft": resolve_input(record["revised"]),
            "expected_roles": expected_input_roles(
                memo_names=[m["file_name"] for m in memos], revised=True
            ),
            "expected_reviewers": record["expected_reviewers"],
            "point_count_bands": record["point_count_bands"],
            "verbatim_probes": record["verbatim_probes"],
            "rubric": record["rubric"],
        },
    )


def _load_dataset() -> MemoryDataset:
    return yaml_dataset(Path(__file__).parent / "dataset.yaml", _record_to_sample)


def check_flags_block(report: HtmlReport) -> tuple[bool, str]:
    """The internal block for the author is there, saying to remove it before sending."""
    found = _BEFORE_SENDING.search(report.raw_text)
    return (
        bool(found),
        "internal block marked to remove before sending"
        if found
        else "no block telling the author to remove it before sending",
    )


@scorer(metrics={name: [mean(), stderr()] for name in MEMO_CHECKS})
def memo_structure() -> Scorer:
    """The shared rules that apply to response memos, plus the internal block."""

    async def score(state: TaskState, target: Target) -> Score:
        report, reason = extract_report(state)
        if report is None:
            return failed_score(MEMO_CHECKS, reason)
        shared = structure_checks(report, state.metadata or {})
        checks = {name: shared[name] for name in MEMO_CHECKS if name in shared}
        checks["flags_block"] = check_flags_block(report)
        return checks_to_score(checks)

    return score


def check_ids_consistent(reports: dict[str, HtmlReport]) -> tuple[bool, str]:
    """Every output carries the same reviewer letters and top-level point IDs."""
    if len(reports) < 2:
        return True, "one output, nothing to compare"
    schemes = {
        output: {
            letter: sorted(numbers)
            for letter, numbers in top_level_ids_by_reviewer(
                find_point_ids(report.raw_text)
            ).items()
        }
        for output, report in reports.items()
    }
    first_output, first = next(iter(schemes.items()))
    differing = [output for output, scheme in schemes.items() if scheme != first]
    if not differing:
        return True, f"the same IDs in all {len(schemes)} outputs"
    return False, "; ".join(f"{o}: {schemes[o]}" for o in [first_output, *differing])


@scorer(metrics={name: [mean(), stderr()] for name in REQUEST_CHECKS})
def request_outputs() -> Scorer:
    """Every requested output came back, with one ID scheme across all of them."""

    async def score(state: TaskState, target: Target) -> Score:
        requested: list[str] = (state.metadata or {})["outputs"]
        reports = reports_by_output(state)
        missing = [output for output in requested if output not in reports]
        return checks_to_score(
            {
                "outputs_delivered": (
                    not missing,
                    f"missing or too short: {missing}" if missing else "all delivered",
                ),
                "ids_consistent": check_ids_consistent(
                    {o: r for o, r in reports.items() if o in requested}
                ),
            }
        )

    return score


# The judged criteria. Three hold for every scenario; `scenario_trap` carries the
# per-scenario text. The key set has to be identical across samples.
RUBRIC_CRITERIA = (
    "replies_match_revision",
    "author_voice",
    "flags_kept_internal",
    "scenario_trap",
)

SHARED_CRITERIA: dict[str, str] = {
    "replies_match_revision": (
        "Every reviewer point the revision answers gets a reply that matches what the revised "
        "draft actually does. Where it was addressed, the reply says concretely what changed and "
        "where, located by content, quoting the new text when it is short. Where it was partly "
        "addressed, it says what was done and what was not. Where it was deliberately not "
        "changed, it gives the reason: scope, document type, or a stated disagreement. A reply "
        "that claims a change the revised draft does not show, or gives a reason the revision "
        "does not support, fails this. A point the revision neither changes nor gives a reason "
        "for is expected to be flagged for the author in the internal block at the top instead "
        "of answered; that handling is judged by another criterion, not here."
    ),
    "author_voice": (
        "Judge only the voice of the replies and the framing the author writes to each "
        "reviewer. Three things are not part of this criterion: the reviewer's own text, "
        "reproduced verbatim as quotes; the internal block for the author at the top, marked to "
        "be removed before sending; and how points left unanswered by the revision are handled, "
        "which another criterion judges. The memos are written as the author to each "
        'reviewer: collegial and plain, opinions owned in the first person ("I" or, for '
        'several authors, "we"), declines given with '
        "a clear reason rather than an apology or reflexive agreement. Each memo is addressed to "
        "one reviewer, carries that reviewer's own header or rating block reframed as a response, "
        "and opens with a short courtesy preamble and a paragraph or two summarizing how the "
        "revision answered them. Sycophancy, hype, filler, or writing as a neutral assessor "
        "instead of the author fails this."
    ),
    "flags_kept_internal": (
        "Any point the revision neither changes nor gives a reason for is flagged for the "
        "author in a single block at the very top, addressed to the author and marked to be "
        "removed before sending, one line per flagged point with its ID and what is missing. "
        "Such a point is quoted in the memo body with no reply under it: no invented reply and "
        "no placeholder such as 'response pending' or a promise to resolve it before sending. "
        "No flag or internal note appears inside the memos themselves. Two things are expected "
        "and are not faults: the block may also list how each uploaded document was read, "
        "since nobody labeled them; and a point the revision partly addresses is answered in "
        "the memo, saying what was done and what was not, rather than flagged."
    ),
}


@scorer(metrics={name: [mean(), stderr()] for name in RUBRIC_CRITERIA})
def rubric_criteria(model: str | Model | None = None) -> Scorer:
    """Grade this suite's four criteria, each in its own grader call, on the rendered text."""

    async def score(state: TaskState, target: Target) -> Score:
        report, reason = extract_report(state)
        if report is None:
            return failed_score(RUBRIC_CRITERIA, reason)
        return await grade_criteria(
            grader=get_model(model) if model else get_model(GRADER_MODEL),
            keys=RUBRIC_CRITERIA,
            criteria=criteria_for(state, SHARED_CRITERIA),
            answer=report.raw_text,
            question=revision_question(state),
        )

    return score


SCORE_LABELS = {
    "verbatim": "Verbatim",
    "quoted": "Quoted",
    "id_scheme": "IDs",
    "self_contained": "Self-cont.",
    "voice": "Voice",
    "flags_block": "Flags",
    "outputs_delivered": "Outputs",
    "ids_consistent": "Same IDs",
    "replies_match_revision": "Replies",
    "author_voice": "Author",
    "flags_kept_internal": "Internal",
    "scenario_trap": "Trap",
    "input_identification": "Inputs",
}


@task
def reviewer_response_memos_e2e():
    return Task(
        dataset=_load_dataset(),
        fail_on_error=0.2,
        solver=review_assistant_solver(timeout_s=_WORKFLOW_TIMEOUT_S),
        scorer=[
            memo_structure(),
            request_outputs(),
            rubric_criteria(),
            input_identification(),
        ],
        viewer=checks_viewer_config(
            [
                *(("memo_structure", name) for name in MEMO_CHECKS),
                *(("request_outputs", name) for name in REQUEST_CHECKS),
                *(("rubric_criteria", name) for name in RUBRIC_CRITERIA),
                ("input_identification", "input_identification"),
            ],
            SCORE_LABELS,
        ),
    )
