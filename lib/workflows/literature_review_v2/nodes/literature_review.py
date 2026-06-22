"""Literature review v2 node — runs a simple deep agent with web search.

Mirrors the v1 literature review goal (surface relevant academic sources the
document may have missed, both supporting and conflicting) but is implemented
with the simple deep-agent pattern: the agent reads the document from `/main.md`
via its tools and returns the standard `AgentCheckResult` output (a list of
`issues` plus a single `report_markdown`).
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


class LiteratureReviewV2Agent(SimpleDeepAgent):
    """Simple deep agent with a longer timeout for the web-search-heavy
    literature review pass."""

    timeout = 600


_SYSTEM_PROMPT = """\
You are an expert literature review researcher reviewing a document.

## Document

The document is available at `/main.md`. Use your tools to read or search its \
content as needed. Use web search to find high-quality academic sources.

## Reporting

Follow the issue-reporting conventions in the issues skill \
(`/skills/issues/SKILL.md`). Report each recommended source as one issue and \
include an overall `report_markdown` summary.\
"""


_USER_PROMPT = PromptTemplate.from_template(
    """
# Role
You are an expert literature review researcher tasked with ensuring an article cites the highest quality and most current sources available. However, if the document publication date is provided, you are only to look for references that come BEFORE the document publication date.

# Goal
Given the full article (available at `/main.md`) and its extracted bibliography, identify references that should be cited or discussed to improve the article. These may be:
- Existing references already listed in the bibliography but not cited in some of the places they should be cited in.
- New, high-quality references found via web research.

# Instructions
1. Read the full document (`/main.md`) and bibliography carefully to understand the existing arguments and cited sources for each.
2. Research relevant high quality references about each topic of discussion and how they could fit in the document as citations.

# Output Format
Return your findings as a list of `issues` plus an overall `report_markdown`.

Create **one issue per recommended reference**, with:
- **title**: A short title naming the suggested source and the recommended action (e.g. "Add citation: Smith et al. 2021").
- **description**: Why this reference should be cited or discussed, including its quality (high, medium, low), direction relative to the document (supporting, conflicting, mixed, contextual), and any political bias (conservative, liberal, other).
- **long_description**: The full details of the recommendation in markdown, including: the authors, publication year, full bibliography citation text, URL or DOI link (if available), the relevant excerpt from the reference, and the relevant excerpt from the main document that relates to it.
- **suggested_action**: What action to take (add a new citation, cite an existing reference in a new place, replace an existing reference, or discuss the reference) and how to implement it.
- **severity**: Use "low" for these recommendations unless a missing or conflicting source is clearly significant, in which case use "medium".
- **start_line** / **end_line**: The 1-indexed line range in `/main.md` of the passage that this reference relates to.

Also provide an overall **report_markdown** summarizing your literature review recommendations (topics of discussion and the references proposed for each).

Remember:
- If the document publication date is provided, you are only to look for references that come BEFORE the document publication date.
- Do not fabricate any references. If relevance to the claims cannot be found, omit the recommendation (do not create an issue for it).

# NOTE:
When generating responses, remove or replace all internal citation tokens such as turn1search0, turn2search3, or similar. Do not display raw reference IDs or metadata markers in the final text. Return clean, human-readable output only.

## Document publication date
{document_publication_date}

## Extracted bibliography
```
{bibliography}
```
"""
)


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

    user_prompt = _USER_PROMPT.invoke(
        {
            "bibliography": bibliography,
            "document_publication_date": document_publication_date,
        }
    ).to_string()

    agent = LiteratureReviewV2Agent(
        context=runtime.context,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tools=[{"type": "web_search"}],
    )
    result, messages = await agent.ainvoke({})

    return {"result": result, "messages": messages}
