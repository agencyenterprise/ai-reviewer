from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from lib.models.agent import Agent


class BibliographyItem(BaseModel):
    text: str = Field(description="The text of the bibliographic item")
    has_associated_supporting_document: bool = Field(
        description="A boolean value indicating whether the bibliographic item has an associated supporting document provided by the user"
    )
    index_of_associated_supporting_document: int = Field(
        description="If the bibliographic item has an associated supporting document, this will be the index of the supporting document in the list of supporting documents provided by the user, otherwise it will be -1."
    )


class ReferenceExtractorResponse(BaseModel):
    references: list[BibliographyItem] = Field(
        description="A list of bibliographic items found in the document"
    )


reference_extractor_agent = Agent(
    name="Reference Extractor",
    description="Extract bibliographic items from a document",
    model="google_genai:gemini-2.5-flash",
    prompt=ChatPromptTemplate.from_template(
        """
# Task
You are a reference extractor. You are given an academic paper text and you need to extract any bibliographic items used in that text.
References are usually found in the bibliography section at the end of the paper.
If there are no references used in the text, return an empty list.

For each bibliographic item, you need to return the following information:
- The text of the bibliographic item
- A boolean value indicating whether the bibliographic item has an associated supporting document provided by the user
- The index of the supporting document in the list of supporting documents provided by the user, if any

## The text to extract bibliographic items from
```
{full_document}
```

## The supporting documents provided by the user
{supporting_documents}
"""
    ),
    mandatory_tools=[],
    output_schema=ReferenceExtractorResponse,
)
