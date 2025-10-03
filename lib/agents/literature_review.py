from enum import Enum
import asyncio
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from lib.models.agent import Agent


class LiteratureReviewResponse(BaseModel):
    report: str = Field(description="A report of the literature review")


_literature_review_agent_prompt = ChatPromptTemplate.from_template(
    """
# Role
You are an expert literature review researcher tasked with ensuring an article cites the strongest and most current sources available.

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
Your report should be formatted in markdown.
Make sure to include a list of relevant references with the following information for each:
- Bibliography item text (Authors, year, title, etc.)
- Publication name
- Publication type (website, journal, book, preprint,etc.)
- Summary of context
- What claims in the document this reference could be related to and refute or support

Remember:
- Do not fabricate any references. If confident support cannot be found, omit the recommendation.
- Format your report in markdown.

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
    output_schema=str,
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
