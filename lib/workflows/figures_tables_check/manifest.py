"""Manifest for the Figures and Tables Check workflow.

Validates that every figure and table in the document is consistent:
- Every figure/table is mentioned in the body text.
- Every figure/table mentioned in the body has an associated image/table present.
- Every figure/table has a title/caption.
- All figures/tables are numbered sequentially or by chapter.

The rules checked live in the `figures-tables-check` skill
(`skills/figures-tables-check/SKILL.md`), which is the single source of truth.
"""

from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest


class FiguresTablesCheckManifest(SimpleDeepAgentManifest):
    """Checks figures and tables for consistency across the document."""

    type = WorkflowRunType.FIGURES_TABLES_CHECK
    name = "Figures & Tables Check"
    description = "Are all figures and tables properly titled, numbered, and referenced? Checks that every figure and table has a title, is consistently numbered, is cited in the body text, and that all body-text references resolve to an actual figure or table in the document."
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]
    is_experimental = False

    skill = "figures-tables-check"

    # Telling a genuine figure from a logo, or finding a caption rendered
    # inside the image, needs the image itself.
    view_images = True
