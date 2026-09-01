"""Log-viewer defaults for this suite: which check regressed, and how stable."""

from inspect_ai.viewer import (
    SampleScoreView,
    SampleScoreViewSort,
    ScoreColorScale,
    TaskSamplesColumn,
    TaskSamplesSort,
    TaskSamplesView,
    ViewerConfig,
)

from evals_inspectai.e2e.results_extraction.contract import (
    INVENTORY_CHECKS,
    RUBRIC_CRITERIA,
)

def viewer_config() -> ViewerConfig:
    """Per-check columns, grouped by sample so repeats sit side by side."""
    score_columns = [
        *(
            TaskSamplesColumn.score("inventory_checks", name)
            for name in INVENTORY_CHECKS
        ),
        *(TaskSamplesColumn.score("rubric_criteria", name) for name in RUBRIC_CRITERIA),
    ]

    return ViewerConfig(
        task_samples_view=TaskSamplesView(
            name="Checks and epochs",
            columns=[
                TaskSamplesColumn(id="sampleStatus"),
                TaskSamplesColumn(id="sampleId"),
                TaskSamplesColumn(id="epoch"),
                *score_columns,
                TaskSamplesColumn(id="error"),
                TaskSamplesColumn(id="duration"),
                TaskSamplesColumn(id="input", visible=False),
                TaskSamplesColumn(id="target", visible=False),
                TaskSamplesColumn(id="answer", visible=False),
                TaskSamplesColumn(id="tokens", visible=False),
            ],
            # Group each document's epochs together: this workflow's failures
            # are run-to-run variance on one document, so repeats of the same
            # sample are the comparison worth reading side by side.
            sort=[
                TaskSamplesSort(column="sampleId", dir="asc"),
                TaskSamplesSort(column="epoch", dir="asc"),
            ],
            compact_scores=True,
            multiline=False,
            score_labels={
                "report": "Report",
                "inventory_table": "Table",
                "result_count": "Count",
                "labels": "Labels",
                "severity_split": "Split",
                "line_ranges": "Lines",
                "no_duplicates": "No dupes",
                "completeness": "Found",
                "class_accuracy": "Class",
                "no_extras": "No extras",
                "severity_ordering": "Order",
                "classification_grounded": "Grounded",
                "sample_expectations": "Sample",
            },
            # Pinned to 0..1 rather than left to the viewer's default, which
            # anchors each palette to that column's observed range: a check that
            # passes everywhere would paint nothing.
            score_color_scales={
                name: ScoreColorScale(palette="good-high", min=0.0, max=1.0)
                for name in (*INVENTORY_CHECKS, *RUBRIC_CRITERIA)
            },
            color_scales_enabled=True,
        ),
        sample_score_view=SampleScoreView(
            default="grid",
            sort=SampleScoreViewSort(column="value", dir="asc"),
        ),
    )

