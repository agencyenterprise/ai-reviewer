from pathlib import Path
from typing import List, Optional

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, json_dataset
from inspect_ai.scorer import Score
from inspect_ai.solver import TaskState
from pydantic import BaseModel, Field

from evals_inspectai.common.api_solver import api_workflow_agent
from evals_inspectai.common.loaders import resolve_input
from evals_inspectai.common.scorers import model_graded_check, structured_output_scorer

# Valid reproducibility classifications (agents/models.py ReproducibilityCategory).
VALID_REPRODUCIBILITY = {
    "fully_reproducible",
    "reproducible_with_web_search",
    "reproducible_with_external_uploads",
    "not_reproducible",
}


class ResultSection(BaseModel):
    title: str = ""
    description: str = ""
    result_type: str = ""
    location: str = ""
    reproducibility: str = ""
    reproducibility_rationale: str = ""


class ResultsListResponse(BaseModel):
    result_sections: List[ResultSection] = Field(default_factory=list)


class ResultsExtractionOutput(BaseModel):
    """Local mirror of ResultsExtractionState.results."""

    results: Optional[ResultsListResponse] = None


def _record_to_sample(record: dict) -> Sample:
    return Sample(
        input=resolve_input(record["input"]),
        target=record.get("target_answer", ""),
        metadata={
            "expected_min_results": record["expected_min_results"],
        },
    )


@task
def results_extraction_e2e():
    dataset = json_dataset(
        str(Path(__file__).parent / "dataset.json"),
        _record_to_sample,
    )

    return Task(
        dataset=dataset,
        fail_on_error=0.2,
        solver=api_workflow_agent("results_extraction", timeout_s=600),
        scorer=[
            structured_output_scorer(ResultsExtractionOutput, _check_results),
            model_graded_check(partial_credit=True),
        ],
    )


def _check_results(output: ResultsExtractionOutput, state: TaskState) -> Score:
    """Verify enough results were extracted and each has a valid reproducibility class.

    Result titles and descriptions are free-form, so we score on the stable
    signal: that at least the expected number of result sections were found and
    every one carries a recognised reproducibility classification.
    """
    expected_min: int = state.metadata["expected_min_results"]
    sections = output.results.result_sections if output.results else []

    if len(sections) < expected_min:
        return Score(
            value=0.0,
            explanation=(
                f"Expected at least {expected_min} result sections, "
                f"got {len(sections)}"
            ),
        )

    invalid = [s for s in sections if s.reproducibility not in VALID_REPRODUCIBILITY]
    if invalid:
        return Score(
            value=0.0,
            explanation=(
                f"{len(invalid)} section(s) have an unrecognised reproducibility "
                f"class, e.g. '{invalid[0].reproducibility}'"
            ),
        )

    return Score(
        value=1.0,
        explanation=(
            f"Extracted {len(sections)} result sections (>= {expected_min}), "
            "all with valid reproducibility classes"
        ),
    )
