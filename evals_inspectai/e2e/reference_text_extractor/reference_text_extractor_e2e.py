"""E2E eval for the Reference Extraction workflow.

Declared by ``skills/reference-extraction/SKILL.md``; runs through the API like
every other e2e eval. The workflow finds the document's reference section and
returns each entry as one string with the lines it spans: entry numbers
removed, repeated-author placeholders resolved to the previous author, and an
entry wrapped over several lines merged into one. Footnotes, endnotes and
in-text citations are not entries, and a document without a reference section
yields none.

Ground truth is ``dataset.yaml``: the entries of each document's reference
section, which the loader checks are the document's own text. Samples cover
numbered, bracketed, bulleted, blank-line separated and hanging-indent lists;
entries wrapped over several lines or onto a URL line; the three placeholder
forms the skill names; headings the skill lists and variants it covers with
"etc." ("Selected Bibliography", "Further Reading") or none at all; two
reference sections in one document; a list followed by appendices; endnotes
before a reference list and endnotes with no reference list; an empty
reference section; a document with no references; and two published RAND
reports (152 and 309 entries) whose conversion split entries across
paragraphs and bullets.

Scorer: ``reference_checks`` (``criteria.py``) pairs the extracted references
one to one with the expected entries, identical texts first and then tolerant
matches, and reports recall, precision, F1, the clean document left alone,
whether each paired text is exactly the entry, whether each extracted text is
in the document at all, and whether the lines it names hold it.

Run (backend must be running)::

    uv run inspect eval evals_inspectai/e2e/reference_text_extractor/reference_text_extractor_e2e.py --epochs 3
"""

from pathlib import Path

from inspect_ai import Task, task

from evals_inspectai.common.api_solver import api_workflow_agent
from evals_inspectai.common.viewer import checks_viewer_config
from evals_inspectai.e2e.reference_text_extractor.criteria import (
    DESCRIPTIONS,
    KEYS,
    SCORE_LABELS,
    reference_checks,
)
from evals_inspectai.e2e.reference_text_extractor.records import reference_dataset

WORKFLOW_TYPE = "reference_extraction"
DATASET = Path(__file__).parent / "dataset.yaml"
SCORER = "reference_checks"


@task
def reference_text_extractor_e2e(timeout_s: float = 600) -> Task:
    """Run Reference Extraction on every sample and score the references it returns.

    Args:
        timeout_s: How long to wait for one workflow run through the API.
    """
    return Task(
        dataset=reference_dataset(DATASET),
        metadata={
            "ground_truth": (
                "The entries of each document's reference section as the skill defines them (entry numbers "
                "removed, repeated-author placeholders resolved, wrapped lines merged), checked at load time to be "
                "the document's own text after normalization. Optional entries neither cost precision nor count "
                "toward recall. A NaN metric value means the sample gave that check nothing to judge."
            ),
            "metrics": {SCORER: DESCRIPTIONS},
        },
        solver=api_workflow_agent(WORKFLOW_TYPE, timeout_s=timeout_s),
        scorer=[reference_checks()],
        fail_on_error=0.2,
        viewer=checks_viewer_config([(SCORER, key) for key in KEYS], SCORE_LABELS),
    )
