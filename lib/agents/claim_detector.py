from pydantic import BaseModel, Field
from lib.models import Agent

from langchain_core.prompts import ChatPromptTemplate


class Claim(BaseModel):
    text: str = Field(
        description="The relevant part of the text within the chunk of text that implies the claims"
    )
    claim: str = Field(description="The claim made in the text")
    rationale: str = Field(
        description="The rationale for why you think the chunk of text implies this claim"
    )
    needs_substantiation: bool = Field(
        description="A boolean value indicating whether the claims needs to be substantiated. If the claim is so obvious that an academic writing would not need to provide a reference for it, then this can be False."
    )


class ClaimResponse(BaseModel):
    claims: list[Claim] = Field(
        description="A list of claims made in the chunk of text"
    )
    rationale: str = Field(
        description="Overall rationale for why you think the chunk of text implies these claims"
    )


claim_detector_agent = Agent(
    name="Claim Detector",
    description="Detect claims in a chunk of text",
    model="openai:gpt-5",
    prompt=ChatPromptTemplate.from_template(
        """
## Task
You are a claim detector. You are given a chunk of text and you need to extract any claims made in that chunk of text.
You will be given a full document and a chunk of text from that document.
You need to return a list of claims made in that chunk of text.
If there are no claims made in the chunk, return an empty list.
For each claim, you need to return the following information:
- The claim
- Your rationale for why you think the chunk of text implies this claim
- A boolean value indicating whether the claims needs to be substantiated

## The full document that the chunk is a part of
```
{full_document}
```

## The chunk of text to extract claims from
```
{chunk}
```
"""
    ),
    mandatory_tools=[],
    output_schema=ClaimResponse,
)
