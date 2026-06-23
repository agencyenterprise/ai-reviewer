"""Literature review v2 node — runs a simple deep agent with web search.

Mirrors the v1 literature review goal (surface relevant academic sources the
document may have missed, both supporting and conflicting) but is implemented
with the simple deep-agent pattern: the agent reads the document from `/main.md`
via its tools and returns the standard `AgentCheckResult` output (a list of
`issues` plus a single `report_markdown`).
"""

import logging
from datetime import date

from langgraph.runtime import Runtime

from lib.agents.formatting_utils import format_bibliography
from lib.skills import load_skill_prompt
from lib.workflows.context import ContextSchema
from lib.workflows.decorators import register_node
from lib.workflows.simple_deep_agent.agent import SimpleDeepAgent
from lib.workflows.simple_deep_agent.state import SimpleDeepAgentState

logger = logging.getLogger(__name__)


class LiteratureReviewV2Agent(SimpleDeepAgent):
    """Simple deep agent with a longer timeout for the web-search-heavy
    literature review pass."""

    timeout = 600


# The literature-review *procedure* is the portable `literature-review` skill
# (the single source of truth). This system prompt carries only the
# Draft-Detective-specific framing: where the document lives and how to map the
# skill's recommendations onto the standard issues output contract.
_SYSTEM_PROMPT = """\
You are an expert literature review researcher reviewing a document.

## Document

The document is available at `/main.md`. Use your tools to read or search its \
content as needed. Use web search to find high-quality academic sources.

## Reporting

Follow the issue-reporting conventions in the issues skill \
(`/skills/issues/SKILL.md`). Report **one issue per recommended source**, mapping \
your recommendation onto the issue fields:
- **title**: name the suggested source and the action (e.g. "Add citation: Smith et al. 2021").
- **description**: why it should be cited or discussed, including its quality \
(high/medium/low) and direction relative to the document (supporting, \
conflicting, mixed, contextual).
- **long_description**: full details in markdown — authors, year, full citation \
text, URL/DOI, the relevant excerpt from the source, and the related excerpt \
from the document.
- **suggested_action**: the action to take (add a new citation, cite an existing \
reference in a new place, replace one, or discuss it) and how to implement it.
- **severity**: "low" by default; "medium" only when a missing or conflicting \
source is clearly significant.
- **start_line** / **end_line**: the 1-indexed line range in `/main.md` of the \
passage the source relates to.

Also include an overall `report_markdown` summarizing the review by topic, with \
the full citation for every recommended source.\
"""


# Backend-injected, per-run inputs appended to the portable skill prompt.
_INPUTS_TEMPLATE = """\

---

## Inputs for this run

### Document publication date
{document_publication_date}

### Extracted bibliography
```
{bibliography}
```
"""


@register_node("Review literature")
async def literature_review(
    state: SimpleDeepAgentState, runtime: Runtime[ContextSchema]
) -> dict:
    file_artifacts_service = runtime.context.file_artifacts_service

    references = await file_artifacts_service.get_extracted_references()
    bibliography = format_bibliography(references)
    document_publication_date = (
        state.config.publication_date
        if state.config.publication_date
        else date.today().isoformat()
    )

    user_prompt = load_skill_prompt("literature-review") + _INPUTS_TEMPLATE.format(
        document_publication_date=document_publication_date,
        bibliography=bibliography,
    )

    agent = LiteratureReviewV2Agent(
        context=runtime.context,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tools=[{"type": "web_search"}],
    )
    result, messages = await agent.ainvoke({})

    return {"result": result, "messages": messages}
