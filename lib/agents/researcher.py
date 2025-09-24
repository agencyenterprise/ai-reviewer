from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from lib.models.agent import Agent


class RelevantInformation(BaseModel):
    text: str = Field(description="The text of the relevant information")
    source: str = Field(
        description="The source of the relevant information, this could be the webpage where this can be found, the citation for the reference"
    )
    related_excerpt: str = Field(
        description="The excerpt from the document that this information is most related to"
    )
    rationale: str = Field(
        description="The rationale for why you think this text is relevant"
    )


class ResearcherResponse(BaseModel):
    results: list[RelevantInformation] = Field(
        description="A list of relevant information found about document"
    )
    rationale: str = Field(
        description="The rationale for why you think these pieces of information are relevant"
    )


research_agent = Agent(
    name="Researcher",
    description="Research the topics discussed in the document and find any relevant more up to date information about them online",
    model="openai:gpt-5",
    prompt=ChatPromptTemplate.from_template(
        """
# Task
You are a researcher. You are given an article and you want to help make sure none of the information in the article is stale, or out of date.
You should search the web about various concepts/statements in the document that seem time dependent and see if there is anything new about them that should be revised/incorporated in the article.

For each new piece of information hat find about a concept/statement in the article, you need to return the following information:
- The text of the new piece of information
- The source of the relevant information, this could be the webpage where this can be found, the citation for the reference
- The excerpt from the document that this information is most related to
- The rationale for why you think this text is relevant

Return as many pieces of information as you think are worth paying attention to. Do as many searches as needed to research them all.

## The text of the article
```
{full_document}
```
"""
    ),
    tools=["web_search"],
    mandatory_tools=["web_search"],
    output_schema=ResearcherResponse,
)


if __name__ == "__main__":
    response = research_agent.apply_sync(
        {
            "full_document": """# Some statistics about the office of the US president
Over the course of the US history, the office of the US president has changed hand dozens of times. Various types of exchanges has happened, ranging from the same president being elected more than twice (i.e., Franklin D. Roosevelt) to the president being removed from office (i.e., Andrew Johnson).

One thing that has never happened, is that a one-term president comes back to office in a later term after losing one reelection bid. So surely, based on this track record alone it seems exceedingly unlikely that former president Trump would be able to defeat President Joe Biden in the 2024 election.
"""
        }
    )
    print(response)
