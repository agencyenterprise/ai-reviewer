from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest


class AdvocacyToneV2Manifest(SimpleDeepAgentManifest):
    """Flags advocacy language, trigger words, and subjective tone via a deep agent."""

    type = WorkflowRunType.ADVOCACY_TONE_V2
    name = "Advocacy & Tone"
    description = (
        "Does your document use neutral, objective language? Flags advocacy "
        "language, trigger words, and subjective tone."
    )
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]
    is_experimental = False

    skill = "advocacy-tone"
