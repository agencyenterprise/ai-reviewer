from enum import Enum
import asyncio
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from lib.config.llm import models
from lib.models.agent import Agent


class ContextType(str, Enum):
    SUPPORTING = "SUPPORTING"
    CONFLICTING = "CONFLICTING"
    CONTEXTUAL = "CONTEXTUAL"


class Reference(BaseModel):
    """A reference that should be cited or discussed in the article"""

    title: str = Field(description="The title of the reference")
    authors: str = Field(description="Authors of the source")
    publication_year: int = Field(description="Year of publication")
    bibliography_info: str = Field(description="Full bibliography citation text")
    reference_type: str = Field(
        description="Publication type (e.g., journal, website, book, preprint)"
    )
    context_type: ContextType = Field(
        description="Type of context: supporting, conflicting, or contextual"
    )
    link: str | None = Field(
        default=None, description="URL or DOI link to the reference"
    )
    related_excerpt: str = Field(
        description="Relevant excerpt from the document that relates to this reference"
    )
    rationale: str = Field(description="Why this reference should be cited")
    recommended_action: str = Field(
        description="What action to take (e.g., ADD_CITATION, VERIFY_CITATION)"
    )
    explanation_for_recommended_action: str = Field(
        description="How to implement the recommended action"
    )


# note (2025-10-14): for the deep research model, the pydantic data models are not used and the format of the
# frontend is not setup to use the existing structure of the models. So we might modify this format.
class LiteratureReviewResponse(BaseModel):
    relevant_references: list[Reference] = Field(
        default_factory=list, description="List of relevant references to cite"
    )
    rationale: str = Field(
        description="Overall rationale for the literature review recommendations"
    )


_literature_review_agent_prompt = ChatPromptTemplate.from_template(
    """
# Role
You are an expert literature review researcher tasked with ensuring an article cites the highest quality and most current sources available. However, if the document publication date is provided, you are only to look for references that come BEFORE the document publication date.

# Goal
Given the full article and its extracted bibliography, identify references that should be cited or discussed to improve the article. These may be:
- Existing references already listed in the bibliography but not cited in some of the places they should be cited in.
- New, high-quality references found via web research.

# Instructions
1. Read the full document and bibliography carefully to understand the existing arguments and cited sources for each.
2. Create a comprehensive report with the following components:
- Information about topics of discussion
- Relevant high quality references about each topic and how they could fit in the document as citations.

# Format
Your report should be formatted in markdown as a bulleted list. Each reference should follow this format:

- **[Authors] ([Year])**, "[Title]". [Publication Name]. ([Publication Type])
**Summary:** [Detailed summary of the reference's key findings and context]
**Relevant to Claims:** [Analysis of how this reference relates to specific claims in the document, including whether it SUPPORTS, CONFLICTS, or CONTEXTUALIZES them]
**Recommended Action:** [What action to take. Possible actions are to add a new citation, cite an existing reference in a new place, replace an existing reference, discuss a reference, or no action.]
**Explanation for Recommended Action:** [How to implement the recommended action]

Don't include any other text in your report. Only the bulleted list of references.

Remember:
- If the document publication date is provided, you are only to look for references that come BEFORE the document publication date.
- Do not fabricate any references. If relevance to the claims cannot be found, omit the recommendation.
- Format your report in markdown.

## Document publication date
{document_publication_date}

## Full article
```
{full_document}
```

## Extracted bibliography
```
{bibliography}
```
"""
)


model_choice = models["o4-mini-deep-research"]

literature_review_agent = Agent(
    name="Literature Review Researcher",
    description="Review a document paragraph against the article bibliography and recent literature to propose citation updates",
    model=models["o4-mini-deep-research"],
    use_responses_api=True,
    use_react_agent=False,
    use_direct_llm_client=True,  # To use open ai tools (openai_web_search, openai_code_interpreter)
    use_background_mode=True,
    prompt=_literature_review_agent_prompt,
    tools=["openai_web_search"],
    mandatory_tools=[],
    output_schema=LiteratureReviewResponse if "deep" not in model_choice else str,
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
                "document_publication_date": "2024-04-01",
            }
        )
    )
    print(response)
