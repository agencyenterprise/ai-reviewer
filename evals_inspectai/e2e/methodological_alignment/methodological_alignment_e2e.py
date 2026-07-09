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


class SummaryAndOutput(BaseModel):
    summary: str = ""
    markdown_output: str = ""


class ReproducibilityCategoryResponse(BaseModel):
    class_value: str = ""
    rationale: str = ""


class MethodologyComparison(BaseModel):
    """Local mirror of MethodologyComparisonResponse (agents/methodology_comparator)."""

    reproducibility: Optional[ReproducibilityCategoryResponse] = None
    extracted_methodology: Optional[SummaryAndOutput] = None
    field_methods_overview: Optional[SummaryAndOutput] = None
    alignment_with_field_practice: Optional[SummaryAndOutput] = None
    methodological_rigor_and_risks: Optional[SummaryAndOutput] = None
    suggestions_for_improvements: Optional[SummaryAndOutput] = None


class MethodologicalAlignmentOutput(BaseModel):
    """Local mirror of MethodologicalAlignmentState.methodology_comparison."""

    methodology_comparison: Optional[MethodologyComparison] = None


def _record_to_sample(record: dict) -> Sample:
    return Sample(
        input=resolve_input(record["input"]),
        target=record.get("target_answer", ""),
    )


@task
def methodological_alignment_e2e():
    dataset = json_dataset(
        str(Path(__file__).parent / "dataset.json"),
        _record_to_sample,
    )

    return Task(
        dataset=dataset,
        fail_on_error=0.2,
        # Web search makes this workflow slower than the document-only checks.
        solver=api_workflow_agent("methodological_alignment", timeout_s=900),
        scorer=[
            structured_output_scorer(MethodologicalAlignmentOutput, _has_analysis),
            model_graded_check(partial_credit=True),
        ],
    )


def _has_analysis(output: MethodologicalAlignmentOutput, state: TaskState) -> Score:
    """Shape check: the workflow produced a comparison with its core sections filled.

    The full comparison is free-form prose, so we score on the stable signal —
    that the analysis ran and populated a reproducibility class plus the
    field-alignment section — rather than exact wording.
    """
    comparison = output.methodology_comparison
    if comparison is None:
        return Score(value=0.0, explanation="No methodology_comparison in output")

    reproducibility = comparison.reproducibility
    alignment = comparison.alignment_with_field_practice
    class_value = reproducibility.class_value if reproducibility else ""
    has_alignment = bool(alignment and alignment.markdown_output.strip())

    if class_value and has_alignment:
        return Score(
            value=1.0,
            explanation=(
                "Comparison present with reproducibility class "
                f"'{class_value}' and a field-alignment section"
            ),
        )
    return Score(
        value=0.0,
        explanation=(
            f"Incomplete comparison (reproducibility={bool(class_value)}, "
            f"alignment={has_alignment})"
        ),
    )
