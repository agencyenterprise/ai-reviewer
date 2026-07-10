from pathlib import Path
from typing import Optional

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, json_dataset
from inspect_ai.scorer import Score
from inspect_ai.solver import TaskState
from pydantic import BaseModel

from evals_inspectai.common.api_solver import api_workflow_agent
from evals_inspectai.common.loaders import resolve_input
from evals_inspectai.common.scorers import model_graded_check, structured_output_scorer

# Minimum characters for a markdown section to count as substantive output.
_MIN_SECTION_CHARS = 200


class Reviewer2Output(BaseModel):
    """Local mirror of Reviewer2State's markdown outputs."""

    peer_review_markdown: Optional[str] = None
    rebuttal_markdown: Optional[str] = None


def _record_to_sample(record: dict) -> Sample:
    return Sample(
        input=resolve_input(record["input"]),
        target=record.get("target_answer", ""),
    )


@task
def reviewer_2_e2e():
    dataset = json_dataset(
        str(Path(__file__).parent / "dataset.json"),
        _record_to_sample,
    )

    return Task(
        dataset=dataset,
        fail_on_error=0.2,
        solver=api_workflow_agent("reviewer_2", timeout_s=600),
        scorer=[
            structured_output_scorer(Reviewer2Output, _produced_review),
            model_graded_check(partial_credit=True),
        ],
    )


def _produced_review(output: Reviewer2Output, state: TaskState) -> Score:
    """Shape check: both the peer review and the rebuttal were produced.

    Reviewer 2 output is free-form prose, so the stable signal is simply that
    both documents exist and are substantive; the model-graded scorer judges
    whether they cover strengths, weaknesses, and next steps.
    """
    review = (output.peer_review_markdown or "").strip()
    rebuttal = (output.rebuttal_markdown or "").strip()

    if len(review) < _MIN_SECTION_CHARS:
        return Score(
            value=0.0,
            explanation=f"Peer review too short or missing ({len(review)} chars)",
        )
    if len(rebuttal) < _MIN_SECTION_CHARS:
        return Score(
            value=0.0,
            explanation=f"Rebuttal too short or missing ({len(rebuttal)} chars)",
        )
    return Score(
        value=1.0,
        explanation=(
            f"Produced peer review ({len(review)} chars) and "
            f"rebuttal ({len(rebuttal)} chars)"
        ),
    )
