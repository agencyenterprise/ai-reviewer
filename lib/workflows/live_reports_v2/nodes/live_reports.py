"""Live reports v2 node — runs a simple deep agent with web search.

Mirrors the v1 Live Reports goal (find sources published *after* the document's
publication date that update or challenge its claims, and produce an addendum)
but is implemented with the simple deep-agent pattern: the agent reads the
document from `/main.md` via its tools and returns the standard
`AgentCheckResult` output (a list of `issues` plus a single `report_markdown`).
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


class LiveReportsV2Agent(SimpleDeepAgent):
    """Simple deep agent with a longer timeout for the web-search-heavy
    live reports pass."""

    timeout = 600


# The live-report *procedure* is the portable `live-reports` skill (the single
# source of truth). This system prompt carries only the Draft-Detective-specific
# framing: where the document lives and how to map the skill's recommendations
# onto the standard issues output contract.
_SYSTEM_PROMPT = """\
You are an expert research analyst producing a "live report" addendum for a document.

## Document

The document is available at `/main.md`. Use your tools to read or search its \
content as needed. Use web search to find newer literature that may update or \
challenge the document's claims.

## Reporting

Follow the issue-reporting conventions in the issues skill \
(`/skills/issues/SKILL.md`). Report **one issue per claim that newer evidence \
would update or strengthen**, mapping your recommendation onto the issue fields:
- **title**: name the affected claim and the action (e.g. "Update claim: X" or "Add citation: Smith et al. 2024").
- **description**: what the newer evidence shows and its direction relative to \
the claim (supporting, conflicting, mixed, contextual).
- **long_description**: full details in markdown — the new source's full citation \
(authors, year, title, venue/publisher, URL/DOI), the relevant excerpt/finding, \
and how it relates to the claim.
- **suggested_action**: what the authors should do (update the claim and how, or \
add a citation) and how to implement it.
- **severity**: "medium" for an actionable update or added citation; "low" for \
purely contextual additions.
- **start_line** / **end_line**: the 1-indexed line range in `/main.md` of the \
claim/passage the update relates to.

Also include an overall `report_markdown` addendum summarizing the most important \
updates, with the full citation for every recommended source. If nothing warrants \
an update, return an empty issue list and a short report saying so.\
"""


# Backend-injected, per-run inputs appended to the portable skill prompt.
_INPUTS_TEMPLATE = """\

---

## Inputs for this run

### Document publication date
{document_publication_date}

### Current bibliography from the document (already cited — do not re-list these)
```
{bibliography}
```
"""


@register_node("Generate live report")
async def live_reports(
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

    user_prompt = load_skill_prompt("live-reports") + _INPUTS_TEMPLATE.format(
        document_publication_date=document_publication_date,
        bibliography=bibliography,
    )

    agent = LiveReportsV2Agent(
        context=runtime.context,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tools=[{"type": "web_search"}],
    )
    run = await agent.ainvoke({})

    return {"result": run.structured_response, "messages": run.messages}
