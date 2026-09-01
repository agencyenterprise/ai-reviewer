"""Manifest for the Reproducibility Check workflow.

Extracts the document's main results and classifies how reproducible each one is
from the information the document itself provides.

The procedure lives in the `reproducibility-check` skill
(`skills/reproducibility-check/SKILL.md`), which is the single source of truth:
it defines what counts as a result and the four reproducibility classes. The
per-result inventory arrives as issues — one per result, the reproducible ones
as informational `none` items — and the summary as the markdown report.
"""

from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest


class ResultsExtractionManifest(SimpleDeepAgentManifest):
    """Classifies each of the document's main results by reproducibility."""

    type = WorkflowRunType.RESULTS_EXTRACTION
    name = "Reproducibility Check"
    description = "Could someone reproduce your results from the document alone? Extracts main results and classifies each by how reproducible it is based on whether the data is present and the methodology is described."
    needs_web_search = False
    is_experimental = True
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]

    skill = "reproducibility-check"

    # Classifying a result means reading the whole document -- appendices
    # included -- before deciding how each missing ingredient could be obtained.
    # At the default effort the same document swung between every result
    # correctly classified and every result collapsed to "not reproducible"
    # across repeats of one eval, so this pass is worth the extra deliberation.
    reasoning_effort = "high"
