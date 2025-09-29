from enum import Enum
import asyncio
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from lib.models.agent import Agent


class ReferenceType(str, Enum):
    WEBPAGE = "webpage"
    BOOK = "book"
    ARTICLE = "article"
    OTHER = "other"


class RecommendedAction(str, Enum):
    ADD_CITATION = "add_citation"
    REPLACE_EXISTING_REFERENCE = "replace_existing_reference"
    DISCUSS_REFERENCE = "discuss_reference"
    NO_ACTION = "no_action"
    OTHER = "other"


class Reference(BaseModel):
    title: str = Field(
        description="Canonical title for the reference exactly as it should appear in the article's bibliography"
    )
    type: ReferenceType = Field(
        description="Format classification for the reference (webpage, book, article, or other)"
    )
    link: str = Field(
        description="Stable URL or DOI that lets the author retrieve the reference quickly"
    )
    bibliography_info: str = Field(
        description="Bibliography entry formatted in the article's style; reuse the existing entry when the source is already in the bibliography"
    )
    related_excerpt: str = Field(
        description="Exact sentence or excerpt from the provided material that should cite or discuss this reference"
    )
    rationale: str = Field(
        description="Brief explanation of why the reference strengthens, updates, or contextualizes the focused paragraph"
    )
    recommended_action: RecommendedAction = Field(
        description=(
            "Action to take for this reference: add_citation, replace_existing_reference, "
            "discuss_reference, no_action, or other"
        )
    )
    explanation_for_recommended_action: str = Field(
        description="Specific guidance for applying the recommended action, including citation placement or text revisions"
    )


class LiteratureReviewResponse(BaseModel):
    relevant_references: list[Reference] = Field(
        description="Ordered list of the most relevant references the author should consider when revising the paragraph"
    )
    rationale: str = Field(
        description="High-level reasoning summarizing how the recommendations improve the paragraph's literature coverage"
    )


_literature_review_agent_prompt = ChatPromptTemplate.from_template(
    """
# Role
You are an expert literature review researcher tasked with ensuring a paragraph cites the strongest and most current sources available.

# Goal
Given the full article, its extracted bibliography, and a paragraph to revise, identify references that should be cited or discussed to improve that paragraph. These may be:
- Existing references already listed in the bibliography but not cited in this paragraph.
- New, high-quality sources found via web research.

# Instructions
1. Read the paragraph in the context of the full document and bibliography to understand the existing argument and cited sources.
2. Reuse relevant bibliography entries whenever they meaningfully support the paragraph but are currently uncited. Quote the entry exactly in `bibliography_info` and include a stable link.
3. Perform focused web research for key claims, statistics, or notable concepts that lack adequate support. Prefer authoritative sources (peer-reviewed articles, reputable institutions) and capture publication details for `bibliography_info`.
4. For every recommended reference:
   - Use `related_excerpt` to quote the precise sentence(s) that should cite or discuss the source.
   - Select `recommended_action` from {{"add_citation", "replace_existing_reference", "discuss_reference", "no_action", "other"}}.
   - In `explanation_for_recommended_action`, describe exactly where to place the citation or how to revise the text (e.g., “Add citation after the sentence describing X” or “Replace the existing citation to Y with this systematic review because …”).
5. Provide only high-impact recommendations (typically 1-5). Avoid duplicates and clearly distinguish whether the source comes from the existing bibliography or is newly discovered.
6. Summarize your overall reasoning in the response `rationale`.
7. Do not fabricate references. If confident support cannot be found, omit the recommendation.

## Full article
```
{full_document}
```

## Extracted bibliography
```
{bibliography}
```

## Focus paragraph
```
{paragraph}
```
"""
)

literature_review_agent = Agent(
    name="Literature Review Researcher",
    description="Review a document paragraph against the article bibliography and recent literature to propose citation updates",
    model="openai:o4-mini-deep-research",
    use_responses_api=True,
    use_react_agent=False,
    use_direct_llm_client=True,  # To use open ai tools (openai_web_search, openai_code_interpreter)
    use_background_mode=True,
    prompt=_literature_review_agent_prompt,
    tools=["openai_web_search"],
    mandatory_tools=[],
    output_schema=LiteratureReviewResponse,
)


if __name__ == "__main__":
    response = asyncio.run(
        literature_review_agent.apply(
            {
                "full_document": """# Some statistics about the office of the US president
Over the course of the US history, the office of the US president has changed hand dozens of times. Various types of exchanges has happened, ranging from the same president being elected more than twice (i.e., Franklin D. Roosevelt) to the president being removed from office (i.e., Andrew Johnson).

One thing that has never happened, is that a one-term president comes back to office in a later term after losing one reelection bid. So surely, based on this track record alone it seems exceedingly unlikely that former president Trump would be able to defeat President Joe Biden in the 2024 election.
""",
                "bibliography": """Foner, E. (2014). Reconstruction: America's Unfinished Revolution, 1863-1877. New York, NY: Harper & Row.
Skowronek, S. (2011). Presidential Leadership in Political Time. Lawrence, KS: University Press of Kansas.
""",
                "paragraph": """One thing that has never happened, is that a one-term president comes back to office in a later term after losing one reelection bid. So surely, based on this track record alone it seems exceedingly unlikely that former president Trump would be able to defeat President Joe Biden in the 2024 election.""",
            }
        )
    )
    print(response)
