"""Manifest for the Methodological Alignment workflow.

Compares the document's methodology against standard practice in its field,
using web search to characterise the field baseline.

The procedure lives in the `methodology-comparison` skill
(`skills/methodology-comparison/SKILL.md`), which is the single source of truth:
it extracts the methodology (per the `methodology-extraction` skill, mounted
alongside it), searches for the field baseline, and compares the two. Each
missing standard component or methodological risk arrives as a line-anchored
issue, and the full comparison -- extracted methodology, field overview,
alignment, rigor and risks, suggestions -- as the markdown report.
"""

from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest


class MethodologicalAlignmentManifest(SimpleDeepAgentManifest):
    """Compares the document's methodology against field practice."""

    type = WorkflowRunType.METHODOLOGICAL_ALIGNMENT
    name = "Methodological Alignment"
    description = "Does your methodology match standard practices in the literature? Uses web search to find standard methods for a topic area, then compares them against your approach."
    needs_web_search = True
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]

    skill = "methodology-comparison"

    # Characterising the field baseline takes several web searches, and each is
    # resolved inside a single model call, so one turn can run well past the
    # default per-call timeout. The comparison agent this replaces ran at 600s.
    llm_timeout = 600
