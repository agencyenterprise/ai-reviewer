from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, json_dataset
from inspect_ai.scorer import Score
from inspect_ai.solver import TaskState

from evals_inspectai.common.api_solver import api_workflow_agent
from evals_inspectai.common.scorers import model_graded_check, structured_output_scorer
from evals_inspectai.common.simple_deep_agent_types import SimpleDeepAgentOutput


def _record_to_sample(record: dict) -> Sample:
    return Sample(
        input=record["input"],
        target=record.get("target_answer", ""),
        metadata={
            "expected_invalid_count": record["expected_invalid_count"],
        },
    )


@task
def inference_validation_v2_e2e():
    dataset = json_dataset(
        str(Path(__file__).parent / "dataset.json"),
        _record_to_sample,
    )

    return Task(
        dataset=dataset,
        fail_on_error=0.2,
        solver=api_workflow_agent("inference_validation_v2", timeout_s=600),
        scorer=[
            structured_output_scorer(SimpleDeepAgentOutput, _compare_invalid_count),
            model_graded_check(partial_credit=True),
        ],
    )


def _compare_invalid_count(output: SimpleDeepAgentOutput, state: TaskState) -> Score:
    """Compare the number of reported invalid inferences to the expected count.

    Every issue this workflow reports is an invalid inference (it emits no
    informational entries for sound reasoning), so the issue count is the count
    of findings. Titles are free-form paraphrases of the flaw, so the count is
    the stable signal to score on.
    """
    expected: int = state.metadata["expected_invalid_count"]
    issues = output.result.issues if output.result else []
    actual = len(issues)

    if actual == expected:
        return Score(
            value=1.0,
            explanation=f"Invalid-inference count matches expected ({expected})",
        )
    return Score(
        value=0.0,
        explanation=f"Expected {expected} invalid inferences, got {actual}",
    )
