from langgraph.graph import StateGraph

from lib.workflows.advocacy_tone_v2.nodes.advocacy_tone import (
    build_advocacy_tone_v2_graph,
)
from lib.workflows.models import WorkflowRunType
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest


class AdvocacyToneV2Manifest(SimpleDeepAgentManifest):
    """Flags advocacy language, trigger words, and subjective tone via a deep agent.

    Reuses the SimpleDeepAgent state/config and issue conversion, but customises
    the graph so the node can inject the deployment's tunable configuration
    (the ``advocacy_tone_v2.config`` app setting) into the `advocacy-tone` skill
    prompt at runtime.
    """

    type = WorkflowRunType.ADVOCACY_TONE_V2
    name = "Advocacy & Tone"
    description = (
        "Does your document use neutral, objective language? Flags advocacy "
        "language, trigger words, and subjective tone."
    )
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]
    is_experimental = False

    def build_graph(self) -> StateGraph:
        return build_advocacy_tone_v2_graph()
