from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from lib.models.agent import Agent
from lib.services.file import File


class ClaimSubstantiationResult(BaseModel):
    is_substantiated: bool = Field(
        description="A boolean value indicating whether the claim is substantiated by the supporting document(s) or not"
    )
    rationale: str = Field(
        description="A brief rationale for why you think the claim is substantiated or not substantiated by the cited supporting document(s)"
    )
    feedback: str = Field(
        description="A brief suggestion on how the issue can be resolved, e.g., by adding more supporting documents or by rephrasing the original chunk, etc."
    )


class ClaimSubstantiationResultWithClaimIndex(ClaimSubstantiationResult):
    chunk_index: int
    claim_index: int


claim_substantiator_agent = Agent(
    name="Claim Substantiator",
    description="Substantiate a claim based on a supporting document",
    model="openai:gpt-5",
    prompt=ChatPromptTemplate.from_template(
        """
# Task
You will be given a chunk of text from a document, a claim that is inferred from that chunk of text, and one or multiple supporting documents that are cited to support the claim.
Your task is to carefully read the supporting document(s) and determine wether the claim is supported by the supporting documents or not. 
Return a rationale for why you think the claim is supported or not supported by the cited supporting document(s).

## The original document from which we are substantiating claims within a chunk
```
{full_document}
```

## The chunk of text from the original document that contains the claim to be substantiated
```
{chunk}
```

## The claim that is inferred from the chunk of text to be substantiated
{claim}

## The list of references cited to support the claim and their associated supporting document (if any)
{cited_references}
"""
    ),
    mandatory_tools=[],
    output_schema=ClaimSubstantiationResult,
)
