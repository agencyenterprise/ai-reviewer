"""E2E eval for the Review Assistant: output first, documents unlabeled.

The author picks outputs and hands over every document they have without
saying which is which. This suite checks what the planning and coverage suites
do not: several outputs from one request, and a reviewer who left only Word
comments. It scores:

- `input_identification`: whether the agent took each document for what it
  is (original draft, revised draft, reviewer memo, marked-up draft, response
  memo), read from the notes it leaves on how it read the inputs.
- `outputs_delivered`: every requested output came back as a real document.
- `report_structure`: the skill's exactly-checkable rules (memos verbatim and
  quoted, the point-ID scheme, self-containment, the two-part layout, voice),
  applied to every delivered output; a check passes only when it holds in all
  of them it applies to (the response memos are exempt from the two-part
  layout, as the skill says). In the comments-only sample, the reviewer who left only Word
  comments must come through as a reviewer of their own, with each comment
  reproduced in a quote and given an ID.

The project is built the way an author would: the reviewed draft is the
project's main document, the rest are uploaded as review documents, and the
request names all of them in the dataset's order, through the same endpoint
the Review Assistant tab calls.

```bash
uv run inspect eval evals_inspectai/e2e/review_assistant/review_assistant_e2e.py
```
"""

import json
from pathlib import Path
from typing import Any

import yaml
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ModelOutput
from inspect_ai.scorer import Score, Scorer, Target, mean, scorer, stderr
from inspect_ai.solver import Generate, Solver, TaskState, solver

from evals_inspectai.common.api_solver import surface_conversations
from evals_inspectai.common.html_report import HtmlReport
from evals_inspectai.common.loaders import resolve_input
from evals_inspectai.common.model_override import output_model_name
from evals_inspectai.common.peer_review_fixture import (
    ReviewDocument,
    build_review_project,
    run_review_request,
)
from evals_inspectai.common.review_assistant_scorers import (
    MIN_REPORT_CHARS,
    STRUCTURE_CHECKS,
    structure_checks,
)
from evals_inspectai.common.scorers import checks_to_score, failed_score
from evals_inspectai.e2e.review_assistant.docx_fixture import (
    FixtureComment,
    marked_up_docx,
)

_TARGET_WORKFLOW = "review_assistant"
_ORIGINAL_DRAFT = "original draft"

# One agent writes up to three long documents at high reasoning effort.
_WORKFLOW_TIMEOUT_S = 3600


def _record_to_sample(record: dict[str, Any]) -> Sample:
    original = next(d for d in record["documents"] if d["role"] == _ORIGINAL_DRAFT)
    return Sample(
        id=record["id"],
        # The reviewed draft is the input, so it reaches the viewer as the question.
        input=resolve_input(original["source"]),
        target=", ".join(record["outputs"]),
        metadata={
            "outputs": record["outputs"],
            "documents": record["documents"],
            "expected_reviewers": record["expected_reviewers"],
            "point_count_bands": record["point_count_bands"],
            "verbatim_probes": record["verbatim_probes"],
        },
    )


def _load_dataset() -> MemoryDataset:
    path = Path(__file__).parent / "dataset.yaml"
    records = yaml.safe_load(path.read_text())
    return MemoryDataset(
        samples=[_record_to_sample(r) for r in records],
        name="review_assistant",
        location=str(path),
    )


def _content(document: dict[str, Any]) -> str | bytes:
    """The bytes to upload: the fixture text, or a Word file built from it."""
    if "marked_up_from" in document:
        return marked_up_docx(
            resolve_input(document["marked_up_from"]),
            author=document["author"],
            comments=[FixtureComment.model_validate(c) for c in document["comments"]],
        )
    text = resolve_input(document["source"])
    if byline := document.get("byline"):
        # Under the memo's title, where a reviewer usually signs it.
        title, _, rest = text.partition("\n")
        return f"{title}\n\n{byline}\n{rest}"
    return text


async def _build_project(documents: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """Create the project and return it with the request's file ids, in dataset order."""
    original = next(d for d in documents if d["role"] == _ORIGINAL_DRAFT)
    others = [d for d in documents if d is not original]
    project_id, ids_by_name = await build_review_project(
        original["file_name"],
        resolve_input(original["source"]),
        [ReviewDocument(d["file_name"], _content(d)) for d in others],
    )
    return project_id, [ids_by_name[d["file_name"]] for d in documents]


@solver
def review_assistant_solver(timeout_s: float = _WORKFLOW_TIMEOUT_S) -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata or {}
        project_id, file_ids = await _build_project(meta["documents"])
        run_detail = await run_review_request(
            project_id, meta["outputs"], file_ids, timeout_s=timeout_s
        )

        workflow_state = run_detail.get("state") or {}
        await surface_conversations(state, workflow_state, _TARGET_WORKFLOW)
        state.output = ModelOutput(
            completion=json.dumps(workflow_state),
            model=output_model_name(run_detail),
        )
        return state

    return solve


def _workflow_state(state: TaskState) -> dict[str, Any]:
    try:
        parsed = json.loads(state.output.completion or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalize_role(role: str) -> str:
    return " ".join(role.lower().replace("-", " ").split())


@scorer(metrics=[mean(), stderr()])
def input_identification() -> Scorer:
    """The share of documents the agent took for what they are."""

    async def score(state: TaskState, target: Target) -> Score:
        workflow_state = _workflow_state(state)
        documents: list[dict[str, Any]] = (state.metadata or {})["documents"]
        folders = {i["file_name"]: i["folder"] for i in workflow_state.get("inputs") or []}
        readings = {r["folder"]: r for r in workflow_state.get("input_readings") or []}

        lines, correct = [], 0
        for document in documents:
            reading = readings.get(folders.get(document["file_name"], ""), {})
            got = _normalize_role(reading.get("role") or "")
            ok = got == _normalize_role(document["role"])
            correct += ok
            lines.append(
                f"{'PASS' if ok else 'FAIL'} {document['file_name']}: "
                f"expected {document['role']!r}, read as {got or 'nothing'!r}"
            )
        return Score(value=correct / len(documents), explanation="\n".join(lines))

    return score


def _reports(state: TaskState) -> dict[str, str]:
    return {
        r["output"]: r.get("report_html") or ""
        for r in _workflow_state(state).get("reports") or []
    }


@scorer(metrics=[mean(), stderr()])
def outputs_delivered() -> Scorer:
    """Every requested output came back as a substantive document."""

    async def score(state: TaskState, target: Target) -> Score:
        reports = _reports(state)
        requested: list[str] = (state.metadata or {})["outputs"]
        missing = [o for o in requested if len(reports.get(o, "")) < MIN_REPORT_CHARS]
        return Score(
            value=0.0 if missing else 1.0,
            explanation=f"missing or too short: {missing}" if missing else "all delivered",
        )

    return score


# Checks an output is exempt from, by the skill's own rules.
_EXEMPT: dict[str, tuple[str, ...]] = {"reviewer_response_memos": ("two_part_layout",)}


@scorer(metrics={name: [mean(), stderr()] for name in STRUCTURE_CHECKS})
def report_structure_all_outputs() -> Scorer:
    """The skill's exact rules, holding in every delivered output.

    The response memos are one document holding a memo per reviewer, so the
    reviewer letters and point IDs they carry are the same scheme as the other
    outputs and are checked the same way. The two-part layout is the exception:
    the skill exempts the response memos from it, since a summary panel written
    for the author would read wrong in a letter to the reviewer.
    """

    async def score(state: TaskState, target: Target) -> Score:
        reports = _reports(state)
        meta = state.metadata or {}
        delivered = {o: html for o, html in reports.items() if len(html) >= MIN_REPORT_CHARS}
        if not delivered:
            return failed_score(STRUCTURE_CHECKS, "No substantive report to check")

        per_output = {o: structure_checks(HtmlReport(html), meta) for o, html in delivered.items()}
        combined: dict[str, tuple[bool, str]] = {}
        for check in STRUCTURE_CHECKS:
            applies = {o: r for o, r in per_output.items() if check not in _EXEMPT.get(o, ())}
            failures = [f"{o}: {r[check][1]}" for o, r in applies.items() if not r[check][0]]
            combined[check] = (
                not failures,
                "; ".join(failures) if failures else f"holds in all {len(applies)} output(s) it applies to",
            )
        return checks_to_score(combined)

    return score


@task
def review_assistant_e2e() -> Task:
    return Task(
        dataset=_load_dataset(),
        solver=review_assistant_solver(),
        scorer=[input_identification(), outputs_delivered(), report_structure_all_outputs()],
    )
