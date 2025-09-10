from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from lib.models.agent import Agent


class ReferenceExtractorResponse(BaseModel):
    references: list[str] = Field(description="A list of references found in the text")


reference_extractor_agent = Agent(
    name="Reference Extractor",
    description="Extract references from a text",
    model="google_genai:gemini-2.5-flash-lite",
    prompt=ChatPromptTemplate.from_template(
        """
# Task
You are a reference extractor. You are given an academic paper text and you need to extract any bibliographic references used in that text.
References are usually found in the bibliography section at the end of the paper.
If there are no references used in the text, return an empty list.

## The text to extract references from
```
{full_document}
```
"""
    ),
    mandatory_tools=[],
    output_schema=ReferenceExtractorResponse,
)
