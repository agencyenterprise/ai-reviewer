from pydantic import BaseModel, Field
from enum import IntEnum
from langchain_core.prompts import ChatPromptTemplate

from lib.models.agent import Agent


class Severity(IntEnum):
    NO_ISSUE = 0
    NOT_ENOUGH_DATA = 1
    MAY_BE_OK = 2
    SHOULD_BE_FIXED = 3
    MUST_BE_FIXED = 4


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
    severity: Severity = Field(
        description=(
            "The severity of the substantiation issue with increasing numeric levels: "
            "0 = no issue, "
            "1 = not enough data to know for sure, "
            "2 = may be ok, "
            "3 = should be fixed, "
            "4 = must be fixed"
        )
    )


class ClaimSubstantiationResultWithClaimIndex(ClaimSubstantiationResult):
    chunk_index: int
    claim_index: int


_claim_substantiator_prompt = ChatPromptTemplate.from_template(
    """
# Task
You will be given a chunk of text from a document, a claim that is inferred from that chunk of text, and one or multiple supporting documents that are cited to support the claim.
Your task is to carefully read the supporting document(s) and determine wether the claim is supported by the supporting documents or not.
Return a rationale for why you think the claim is supported or not supported by the cited supporting document(s).

For each claim that has a substantiation issue, also output a numeric severity level based on the following definitions:
- 0 (no issue): There are no issues with the substantiation of the claim.
- 1 (not enough data to know for sure): Insufficient or ambiguous evidence to decide.
- 2 (may be ok): Minor concerns or nitpicks, likely acceptable but could be improved.
- 3 (should be fixed): Clear issues that should probably be addressed before publication.
- 4 (must be fixed): Critical problems; claim is unsupported or contradicted and must be corrected.

You MUST include the "severity" field in your output using one of the numeric values 1, 2, 3, or 4 as defined above.

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
)

claim_substantiator_agent = Agent(
    name="Claim Substantiator",
    description="Substantiate a claim based on a supporting document",
    model="openai:gpt-5",
    prompt=_claim_substantiator_prompt,
    tools=[],
    mandatory_tools=[],
    output_schema=ClaimSubstantiationResult,
)
