"""Advocacy & Tone v2 node — a SimpleDeepAgent driven by the `advocacy-tone`
skill, with the deployment's tunable configuration injected at runtime.

The skill is the portable *method*; the `advocacy_tone_v2.config` app setting is
the deployment's *data* (trigger words, advocacy phrases, ignored sections,
issue-type definitions). The node loads the skill and appends the configuration
so admins can tune the check via the app-config UI without touching code.
"""

import logging
from typing import Optional

from langgraph.graph import START, StateGraph
from langgraph.graph.state import END
from langgraph.runtime import Runtime

from lib.services.app_configs import get_config
from lib.skills import load_skill_prompt
from lib.workflows.advocacy_tone_v2.config_keys import ADVOCACY_TONE_V2_CONFIG_KEY
from lib.workflows.context import ContextSchema
from lib.workflows.decorators import register_node
from lib.workflows.simple_deep_agent.agent import SimpleDeepAgent
from lib.workflows.simple_deep_agent.state import SimpleDeepAgentState

logger = logging.getLogger(__name__)

_CONFIG_HEADER = """\

---

## Configuration for this deployment

Use the trigger words, advocacy phrases, sections to skip, and issue-type \
definitions below for this review. They supersede the example lists and \
definitions in the sections above.

"""


def build_user_prompt(config_text: Optional[str]) -> str:
    """Compose the agent user prompt: the portable skill + the deployment config.

    Falls back to the skill alone (its built-in defaults) when no config is set.
    """
    prompt = load_skill_prompt("advocacy-tone")
    if config_text and config_text.strip():
        prompt += _CONFIG_HEADER + config_text.strip() + "\n"
    return prompt


@register_node("Detect advocacy & tone")
async def detect_advocacy_tone(
    state: SimpleDeepAgentState, runtime: Runtime[ContextSchema]
) -> dict:
    config_text = await get_config(ADVOCACY_TONE_V2_CONFIG_KEY)
    agent = SimpleDeepAgent(
        context=runtime.context,
        user_prompt=build_user_prompt(config_text),
    )
    result, messages = await agent.ainvoke({})
    return {"result": result, "messages": messages}


def build_advocacy_tone_v2_graph() -> StateGraph:
    graph = StateGraph(SimpleDeepAgentState, context_schema=ContextSchema)
    graph.add_node("detect_advocacy_tone", detect_advocacy_tone)
    graph.add_edge(START, "detect_advocacy_tone")
    graph.add_edge("detect_advocacy_tone", END)
    return graph  # type: ignore[return-value]
