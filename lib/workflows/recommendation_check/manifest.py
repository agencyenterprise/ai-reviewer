"""Manifest for the Recommendation Check workflow.

Verifies that recommendations made in the document are directly supported by
the findings/evidence presented elsewhere in the same document. Complements
citation-grounding workflows: those check that claims are backed by external
sources; this one checks that recommendations are backed by the document's
own findings.

The rules checked live in the `recommendation-check` skill
(`skills/recommendation-check/SKILL.md`), which is the single source of truth.
"""

from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest


class RecommendationCheckManifest(SimpleDeepAgentManifest):
    """Checks that recommendations are supported by the document's own findings."""

    type = WorkflowRunType.RECOMMENDATION_CHECK
    name = "Recommendation Check"
    description = (
        "Are the document's recommendations supported by its own findings? "
        "Flags recommendations that lack backing evidence in the body, or "
        "where the evidence is weak, indirect, or contradictory."
    )
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]
    is_experimental = True

    skill = "recommendation-check"

    # A recommendation's supporting finding is sometimes only in a figure.
    view_images = True
