"""Manifest for the Document Structure workflow.

Checks that a document contains all required top-level sections:
About This, Acknowledgements, Methods, Results, Conclusion, References,
and Appendix (only flagged as missing if referenced in the body text).

The rules checked live in the `document-contents` skill
(`skills/document-contents/SKILL.md`), which is the single source of truth.
"""

from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest


class DocumentStructureManifest(SimpleDeepAgentManifest):
    """Checks that a document contains all required structural sections."""

    type = WorkflowRunType.DOCUMENT_STRUCTURE
    name = "Document Contents"
    description = "Does your document include all required content? Checks that key content is present in the document: About This, Acknowledgements, Methods, Results, Conclusion, References, and Appendix (when referenced in the text)."
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]
    is_experimental = False

    skill = "document-contents"
