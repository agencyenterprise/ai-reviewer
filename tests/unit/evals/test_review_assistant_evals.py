"""The review-assistant eval suites: their datasets and the checks they share."""

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from inspect_ai.dataset import Sample
from inspect_ai.model import ModelName, ModelOutput
from inspect_ai.scorer import Target
from inspect_ai.solver import TaskState

from evals_inspectai.common import peer_review_fixture
from evals_inspectai.common.docx_fixture import MarkedUpCopy
from evals_inspectai.common.html_report import HtmlReport
from evals_inspectai.common.peer_review_fixture import (
    DRAFT_FILE_NAME,
    REVISED_DRAFT_FILE_NAME,
    ReviewDocument,
    expected_input_roles,
    review_assistant_solver,
)
from evals_inspectai.common.review_assistant_scorers import (
    extract_report,
    input_identification,
)
from evals_inspectai.e2e.reviewer_coverage_report.reviewer_coverage_report_e2e import (
    _load_dataset as coverage_dataset,
)
from evals_inspectai.e2e.reviewer_response_memos.reviewer_response_memos_e2e import (
    _load_dataset as memos_dataset,
)
from evals_inspectai.e2e.reviewer_response_memos.reviewer_response_memos_e2e import (
    check_flags_block,
    check_ids_consistent,
)
from evals_inspectai.e2e.revision_planning_summary.revision_planning_summary_e2e import (
    _load_dataset as planning_dataset,
)
from lib.services.docx.review_markup import read_docx_review_markup


def _state(workflow_state: dict, metadata: dict) -> TaskState:
    state = TaskState(
        model=ModelName("mockllm/model"),
        sample_id="s",
        epoch=1,
        input="draft",
        messages=[],
        metadata=metadata,
    )
    state.output = ModelOutput(completion=json.dumps(workflow_state))
    return state


def _html(*paragraphs: str) -> HtmlReport:
    return HtmlReport(
        "<html><body>" + "".join(f"<p>{p}</p>" for p in paragraphs) + "</body></html>"
    )


def _meta(sample: Sample) -> dict[str, Any]:
    return sample.metadata or {}


async def _requested(sample: Sample) -> tuple[list[str], list[str]]:
    """Run the shared solver on a sample with the API patched out; return the
    file names it uploads after the draft and the outputs it asks for."""
    seen: dict[str, Any] = {}

    async def build(
        main_file_name: str, main_markdown: str, documents: list[ReviewDocument]
    ) -> tuple[str, dict[str, str]]:
        seen["names"] = [d.file_name for d in documents]
        names = [main_file_name, *seen["names"]]
        return "project", {n: n for n in names}

    async def run(project_id: str, outputs: list[str], *_: Any, **__: Any) -> dict:
        seen["outputs"] = outputs
        return {"state": {"reports": []}}

    async def surface(*_: Any) -> None:
        return None

    state = TaskState(
        model=ModelName("mockllm/model"),
        sample_id=sample.id or "s",
        epoch=1,
        input=sample.input,
        messages=[],
        metadata=_meta(sample),
    )
    with (
        patch.object(peer_review_fixture, "build_review_project", build),
        patch.object(peer_review_fixture, "run_review_request", run),
        patch.object(peer_review_fixture, "surface_conversations", surface),
    ):
        state = await review_assistant_solver(timeout_s=1)(state, AsyncMock())
    assert json.loads(state.output.completion) == {"reports": []}
    return seen["names"], seen["outputs"]


def test_every_suite_names_its_documents_and_their_roles() -> None:
    for dataset in (planning_dataset(), coverage_dataset(), memos_dataset()):
        for sample in dataset:
            roles = _meta(sample)["expected_roles"]
            assert roles[DRAFT_FILE_NAME] == "original draft", sample.id
            assert (
                "reviewer memo" in roles.values() or "marked-up draft" in roles.values()
            )


def test_the_comparing_suites_hand_over_a_revised_draft() -> None:
    for sample in [*coverage_dataset(), *memos_dataset()]:
        assert (
            _meta(sample)["expected_roles"][REVISED_DRAFT_FILE_NAME] == "revised draft"
        )


def test_the_planning_suite_carries_a_comments_only_reviewer(tmp_path) -> None:
    sample = next(
        s for s in planning_dataset() if s.id == "hiring_audits_comments_only_reviewer"
    )
    meta = _meta(sample)
    [copy] = [MarkedUpCopy.model_validate(m) for m in meta["marked_up"]]
    assert meta["expected_roles"][copy.file_name] == "marked-up draft"
    assert "Reviewer: Prof. Alan Ruiz" in meta["memos"][0]["content"]

    path = tmp_path / copy.file_name
    path.write_bytes(copy.content())
    markup = read_docx_review_markup(str(path))
    assert [c.author for c in markup.comments] == ["Dana Lee"] * 3


def test_only_the_all_outputs_sample_asks_for_more_than_one() -> None:
    many = [s.id for s in memos_dataset() if len(_meta(s)["outputs"]) > 1]
    assert many == ["hiring_audits_all_outputs"]


@pytest.mark.asyncio
async def test_identification_scores_each_document_against_its_role() -> None:
    roles = expected_input_roles(["memo.md"], revised=True)
    workflow_state = {
        "inputs": [
            {"file_name": DRAFT_FILE_NAME, "folder": "/inputs/01-report"},
            {"file_name": "memo.md", "folder": "/inputs/02-memo"},
            {"file_name": REVISED_DRAFT_FILE_NAME, "folder": "/inputs/03-report-1"},
        ],
        "input_readings": [
            {"folder": "/inputs/01-report/", "role": "Original draft"},
            {"folder": "/inputs/02-memo", "role": "reviewer memo"},
            {"folder": "/inputs/03-report-1", "role": "original draft"},
        ],
    }

    score = await input_identification()(
        _state(workflow_state, {"expected_roles": roles}), Target("")
    )

    assert score is not None
    assert score.value == pytest.approx(2 / 3)
    assert "FAIL report (1).md" in (score.explanation or "")


def test_the_sample_reads_its_own_output_among_several() -> None:
    long = "x" * 2500
    workflow_state = {
        "reports": [
            {
                "output": "revision_planning_summary",
                "report_html": f"<p>plan {long}</p>",
            },
            {
                "output": "reviewer_response_memos",
                "report_html": f"<p>memos {long}</p>",
            },
        ]
    }
    report, reason = extract_report(
        _state(workflow_state, {"output": "reviewer_response_memos"})
    )
    assert report is not None and "memos" in report.raw_text, reason


def test_ids_must_match_across_outputs() -> None:
    plan = _html("A1 first.", "A2 second.", "B1 third.")
    same = _html("A1 again.", "A2 again.", "B1 again.")
    short = _html("A1 only.", "B1 only.")

    assert check_ids_consistent({"plan": plan, "memos": same})[0]
    assert not check_ids_consistent({"plan": plan, "memos": short})[0]
    assert check_ids_consistent({"memos": short}) == (
        True,
        "one output, nothing to compare",
    )


def test_the_flags_block_is_found_by_its_instruction() -> None:
    assert check_flags_block(
        _html("For the author: remove this block before sending.")
    )[0]
    assert not check_flags_block(_html("Dear reviewer, thank you."))[0]


@pytest.mark.asyncio
async def test_the_solver_uploads_each_suites_documents_and_asks_for_its_outputs() -> (
    None
):
    planning = {s.id: s for s in planning_dataset()}
    names, outputs = await _requested(planning["hiring_audits_comments_only_reviewer"])
    copy = MarkedUpCopy.model_validate(
        _meta(planning["hiring_audits_comments_only_reviewer"])["marked_up"][0]
    )
    assert names[-1] == copy.file_name
    assert outputs == ["revision_planning_summary"]

    for sample in coverage_dataset():
        meta = _meta(sample)
        names, outputs = await _requested(sample)
        assert names == [
            *(m["file_name"] for m in meta["memos"]),
            REVISED_DRAFT_FILE_NAME,
            *(m["file_name"] for m in meta["response_memos"]),
        ]
        assert outputs == ["reviewer_coverage_report"]

    many = next(s for s in memos_dataset() if s.id == "hiring_audits_all_outputs")
    _, outputs = await _requested(many)
    assert outputs == _meta(many)["outputs"] and len(outputs) > 1
