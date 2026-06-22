"""Live reports v2 node — runs a simple deep agent with web search.

Mirrors the v1 Live Reports goal (find sources published *after* the document's
publication date that update or challenge its claims, and produce an addendum)
but is implemented with the simple deep-agent pattern: the agent reads the
document from `/main.md` via its tools and returns the standard
`AgentCheckResult` output (a list of `issues` plus a single `report_markdown`).
"""

import logging
from datetime import date

from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from lib.agents.formatting_utils import format_bibliography
from lib.workflows.context import ContextSchema
from lib.workflows.decorators import register_node
from lib.workflows.simple_deep_agent.agent import SimpleDeepAgent
from lib.workflows.simple_deep_agent.state import SimpleDeepAgentState

logger = logging.getLogger(__name__)


class LiveReportsV2Agent(SimpleDeepAgent):
    """Simple deep agent with a longer timeout for the web-search-heavy
    live reports pass."""

    timeout = 600


_SYSTEM_PROMPT = """\
You are an expert research analyst producing a "live report" addendum for a document.

## Document

The document is available at `/main.md`. Use your tools to read or search its \
content as needed. Use web search to find newer literature that may update or \
challenge the document's claims.

## Reporting

Follow the issue-reporting conventions in the issues skill \
(`/skills/issues/SKILL.md`). Report each claim that newer evidence would update \
or strengthen as one issue, and include an overall `report_markdown` addendum.\
"""


_USER_PROMPT = PromptTemplate.from_template(
    """
# Role
You are an expert literature review researcher specializing in finding newer evidence that could update or contextualize existing claims in academic and policy documents.

# Goal
Read the document at `/main.md` and identify its central claims. For those claims, use web search to find high-quality literature published AFTER the document's publication date that supports, conflicts with, updates, or adds important context to the claim. Then produce an addendum report describing what the authors should update and why.

# Instructions
1. Identify the document's central claims by reading `/main.md`.
2. For each central claim, search the web for relevant, high-quality sources published AFTER the document publication date ({document_publication_date}). Classify each source's direction relative to the claim: supporting, conflicting, mixed, or contextual.
3. Prioritize peer-reviewed academic sources, government/NGO reports, and reputable institutions. Prefer meta-analyses, systematic reviews, and large-scale studies. Focus on the highest-quality and most relevant sources.
4. Do NOT include sources published before the document publication date, and do NOT re-list sources already present in the document's bibliography below.

# Output Format
Return your findings as a list of `issues` plus an overall `report_markdown` addendum.

Create **one issue per claim that newer evidence would update or strengthen**, with:
- **title**: A short title naming the affected claim and the recommended action (e.g. "Update claim: X" or "Add citation: Smith et al. 2024").
- **description**: What the newer evidence shows and its direction relative to the claim (supporting, conflicting, mixed, contextual).
- **long_description**: The full details in markdown, including the new source's **full citation** (authors, year, title, venue/publisher, and a URL or DOI link when available), the relevant excerpt or finding, and how it relates to the claim.
- **suggested_action**: What the authors should do — update the claim (and how), or add a citation — and how to implement it.
- **severity**: Use "medium" for an actionable update or added citation; use "low" for purely contextual additions.
- **start_line** / **end_line**: The 1-indexed line range in `/main.md` of the claim/passage this update relates to.

Also provide an overall **report_markdown** addendum that summarizes the most important updates (what to change, how, and why it matters) and includes the **full citation / bibliography entry** for every recommended source (authors, year, title, venue, DOI or URL), so the reader can see at a glance how to find each source.

Remember:
- Only consider sources published AFTER the document publication date ({document_publication_date}).
- Only analyze substantive empirical, scientific, or factual claims that newer research could realistically update. If the document makes no such claims (for example an internal note, administrative memo, or opinion piece), do not invent updates — return an empty issue list and a short report stating that no newer evidence is warranted.
- Do not fabricate any references. If no newer evidence warrants a change for a claim, omit it (do not create an issue for it). If nothing warrants an update, return an empty issue list and a short report saying so.

# NOTE:
When generating responses, remove or replace all internal citation tokens such as turn1search0, turn2search3, or similar. Do not display raw reference IDs or metadata markers in the final text. Return clean, human-readable output only.

## Document publication date
{document_publication_date}

## Current bibliography from the document (already cited — do not re-list these)
```
{bibliography}
```
"""
)


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

    user_prompt = _USER_PROMPT.invoke(
        {
            "bibliography": bibliography,
            "document_publication_date": document_publication_date,
        }
    ).to_string()

    agent = LiveReportsV2Agent(
        context=runtime.context,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tools=[{"type": "web_search"}],
    )
    result, messages = await agent.ainvoke({})

    return {"result": result, "messages": messages}
