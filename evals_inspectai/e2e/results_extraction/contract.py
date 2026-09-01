"""What the Reproducibility Check is required to deliver, as constants.

The reproducibility labels, the metric names, and the severity/importance
vocabularies the ground truth is written in. Kept apart from the checks so the
metric contract can be read on its own -- Inspect raises when a declared metric
key is missing from a score, so this tuple and the checks have to agree exactly.
"""

MIN_REPORT_CHARS = 400

# The four reproducibility labels, as they appear in an issue title's trailing
# parenthesis: `Result: <title> (<label>)`.
REPRODUCIBILITY_LABELS = (
    "fully reproducible",
    "reproducible with web search",
    "reproducible with external uploads",
    "not reproducible",
)

# Anything reproducible -- even only with web search or external uploads -- is
# informational; only "not reproducible" carries a real severity.
NOT_REPRODUCIBLE = "not reproducible"
REAL_SEVERITIES = {"low", "medium", "high"}

# One key per deterministic rule.
INVENTORY_CHECKS = (
    "report",
    "inventory_table",
    "result_count",
    "labels",
    "severity_split",
    "line_ranges",
    "no_duplicates",
    "completeness",
    "class_accuracy",
    "no_extras",
    "severity_ordering",
)

# The judged criteria. One holds for every sample; `sample_expectations`
# carries the dataset's own per-sample rubric. The key set has to be identical
# across samples, because Inspect raises when a declared metric key is missing
# from any score.
RUBRIC_CRITERIA = (
    "classification_grounded",
    "sample_expectations",
)

def severity_matches_label(severity: str, label: str) -> bool:
    """The split the skill mandates, without pinning the exact level."""
    if label == NOT_REPRODUCIBLE:
        return severity in REAL_SEVERITIES
    return severity == "none"


# Reproducibility classes as the dataset spells them, mapped to the label that
# appears in an issue title.
CLASS_LABELS = {
    "fully_reproducible": "fully reproducible",
    "reproducible_with_web_search": "reproducible with web search",
    "reproducible_with_external_uploads": "reproducible with external uploads",
    "not_reproducible": "not reproducible",
}

# How much the document rests on a result, most to least. Only compared between
# non-reproducible results, and only as an ordering.
IMPORTANCE_RANK = {"central": 3, "supporting": 2, "incidental": 1}

SEVERITY_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}
