"""Run every end-to-end benchmark for five epochs with Inspect Flow.

This intentionally excludes ``active_voice_judge_calibration``: it is a grader
calibration utility, not an end-to-end product benchmark.

Usage:
    uv run flow run evals_inspectai/flow_config/run_all_evals.py --dry-run
    uv run flow run evals_inspectai/flow_config/run_all_evals.py
"""

from pathlib import Path

from inspect_flow import FlowOptions, FlowSpec, FlowTask

_ROOT = Path(__file__).resolve().parents[2]
_MODEL = "openai/gpt-5.6-terra-2026-07-09"

TASKS = (
    "abbreviation_checker/abbreviation_checker_e2e.py@abbreviation_checker_e2e",
    "abbreviation_checker/abbreviation_checker_report_e2e.py@abbreviation_checker_report_e2e",
    "about_this_ger/about_this_ger_e2e.py@about_this_ger_e2e",
    "active_voice/active_voice_e2e.py@active_voice_e2e",
    "advocacy_tone_v2/advocacy_tone_v2_e2e.py@advocacy_tone_v2_e2e",
    "audience_fit/audience_fit_e2e.py@audience_fit_e2e",
    "claim_reference_validation_v2/claim_reference_validation_v2_e2e.py@claim_reference_validation_v2_e2e",
    "concision_precision/concision_precision_e2e.py@concision_precision_e2e",
    "document_structure/document_structure_e2e.py@document_structure_e2e",
    "figures_tables_check/figures_tables_check_e2e.py@figures_tables_check_e2e",
    "headers_skimmability/headers_skimmability_e2e.py@headers_skimmability_e2e",
    "inference_validation_v2/inference_validation_v2_e2e.py@inference_validation_v2_e2e",
    "literature_review_v2/literature_review_v2_e2e.py@literature_review_v2_e2e",
    "live_reports_v2/live_reports_v2_e2e.py@live_reports_v2_e2e",
    "methodological_alignment/methodological_alignment_e2e.py@methodological_alignment_e2e",
    "narrative_synthesis/narrative_synthesis_e2e.py@narrative_synthesis_e2e",
    "recommendation_check/recommendation_check_e2e.py@recommendation_check_e2e",
    "reference_downloader/reference_downloader_e2e.py@reference_downloader_e2e",
    "reference_text_extractor/reference_text_extractor_e2e.py@reference_text_extractor_e2e",
    "reference_validation_v2/reference_validation_v2_e2e.py@reference_validation_v2_e2e",
    "results_extraction/results_extraction_e2e.py@results_extraction_e2e",
    "reviewer_2/reviewer_2_e2e.py@reviewer_2_e2e",
    "reviewer_coverage_report/reviewer_coverage_report_e2e.py@reviewer_coverage_report_e2e",
    "revision_planning_summary/revision_planning_summary_e2e.py@revision_planning_summary_e2e",
    "writing_consistency/writing_consistency_e2e.py@writing_consistency_e2e",
)


def flow(
    api_base_url: str = "http://127.0.0.1:8000",
    epochs: int = 5,
    max_tasks: int = 1,
    max_samples: int = 2,
) -> FlowSpec:
    """Build the complete five-epoch benchmark run against an existing API."""
    e2e = _ROOT / "evals_inspectai" / "e2e"
    return FlowSpec(
        log_dir=str(_ROOT / "logs" / "all-benchmarks-5-epochs"),
        env={"EVAL_API_BASE_URL": api_base_url},
        # Flow's task and sample limits multiply. Serialize benchmark tasks so
        # agent-heavy workflows do not overwhelm the shared model gateway.
        options=FlowOptions(
            max_tasks=max_tasks,
            max_samples=max_samples,
            log_dir_allow_dirty=True,
        ),
        tasks=[
            FlowTask(name=str(e2e / task), model=_MODEL, epochs=epochs)
            for task in TASKS
        ],
    )
