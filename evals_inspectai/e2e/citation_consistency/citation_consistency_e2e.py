"""E2E eval for the Citations & Reference List workflow.

The workflow is declared by its skill (``skills/citation-consistency/SKILL.md``)
and runs through the API like every other e2e eval. Ground truth is
``dataset.yaml`` in inventory form: the issues a correct run reports, each
anchored on the verbatim citation or reference entry and with edit
expectations, plus correct citations it must leave alone
(``evals_inspectai/common/issue_inventory.py``).

Every check is deterministic: detection, title, severity and edit phrases from
``issue_checks``, and false positives by reason from ``decoy_checks``. Reports
pair one to one with expected issues, since a paragraph often holds several
faulty citations and each must be reported on its own.

``edit_keeps_numbers_and_markers`` is skipped: it checks that an edit keeps
every citation of the original, and this workflow's edits rewrite a citation by
design (a year fixed, *et al.* expanded). The samples' ``must_include`` phrases
carry its guarantee instead: a page number, a *see* and a footnote callout next
to a fixed citation must survive the edit.

The last sample is a 471-line report (``files/long_report.md``), long enough
for the skill's sub-agent path; it takes about two minutes, against well under
one for the others.

Run (backend must be running)::

    uv run inspect eval evals_inspectai/e2e/citation_consistency/citation_consistency_e2e.py
    uv run inspect eval evals_inspectai/e2e/citation_consistency/citation_consistency_e2e.py --sample-id=2
"""

from pathlib import Path

from inspect_ai import Task, task

from evals_inspectai.common.api_solver import api_workflow_agent
from evals_inspectai.common.inventory_suite import InventorySuite

WORKFLOW_TYPE = "citation_consistency"
DATASET = Path(__file__).parent / "dataset.yaml"
GROUND_TRUTH = (
    "Inventory: one expected issue per faulty citation or uncited reference entry, anchored on its verbatim "
    "text, plus document-level issues (mixed systems, missing reference list) matched on title alone, and "
    "decoys for each exclusion the skill states. A NaN metric value means the sample gave that check nothing "
    "to judge."
)


@task
def citation_consistency_e2e(timeout_s: float = 900) -> Task:
    """Run Citations & Reference List on every sample and score it against the inventory.

    Args:
        timeout_s: How long to wait for one workflow run through the API.
    """
    suite = InventorySuite.load(
        DATASET,
        pairing="one_to_one",
        skip_checks=("edit_keeps_numbers_and_markers",),
    )
    return Task(
        dataset=suite.dataset(),
        metadata=suite.metadata(GROUND_TRUTH),
        solver=api_workflow_agent(WORKFLOW_TYPE, timeout_s=timeout_s),
        scorer=suite.scorers(),
        fail_on_error=0.2,
        viewer=suite.viewer(),
    )
