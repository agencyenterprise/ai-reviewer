from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from lib.config.llm import models
from lib.models import Agent


class ToulminClaim(BaseModel):
    text: str = Field(
        description="The exact excerpt from the chunk that implies the claim"
    )
    claim: str = Field(description="The claim made in the excerpt")
    rationale: str = Field(
        description="Why the excerpt implies this claim (brief analytic rationale)"
    )
    needs_substantiation: bool = Field(
        description=(
            "Whether this claim should be substantiated with citations in academic writing. Set to False for common knowledge, basic definitions, logical deductions, or well-established facts in the domain."
        )
    )

    # Toulmin elements
    data: list[str] = Field(
        default_factory=list,
        description=(
            "Data/Grounds: evidence or facts supporting the claim, quoted or paraphrased"
        ),
    )
    warrants: list[str] = Field(
        default_factory=list,
        description=(
            "Warrants: assumptions that connect the data to the claim (may be cultural, logical, or methodological)"
        ),
    )
    warrant_expression: Literal["stated", "implied", "none"] = Field(
        description=(
            "Whether the primary warrant is stated explicitly, implied implicitly, or none could be identified"
        )
    )
    qualifiers: list[str] = Field(
        default_factory=list,
        description=(
            "Qualifiers: words/phrases indicating the strength/scope of the claim (e.g., 'likely', 'some', 'in many cases')"
        ),
    )
    rebuttals: list[str] = Field(
        default_factory=list,
        description=(
            "Rebuttals: acknowledged exceptions, counter-arguments, or conditions under which the claim may not hold"
        ),
    )
    backing: list[str] = Field(
        default_factory=list,
        description=(
            "Backing: additional support that justifies the warrant (e.g., principles, studies, or theoretical reasons)"
        ),
    )


class ToulminClaimResponse(BaseModel):
    claims: list[ToulminClaim] = Field(
        description="List of extracted claims with Toulmin elements when available"
    )
    rationale: str = Field(
        description="Overall rationale for the extractions and how the Toulmin elements were identified"
    )


toulmin_claim_detector_agent = Agent(
    name="Claim Detector (Toulmin)",
    description=(
        "Detect claims in a chunk of text and extract Toulmin elements: data/grounds,"
        " warrants (stated or implied), qualifiers, rebuttals, and backing."
    ),
    model=models["gpt-5"],
    prompt=ChatPromptTemplate.from_template(
        (
            """
## Task
You are a claim detector using the Toulmin model of argumentation. You will receive the full document (context) and a specific chunk. Extract any claims present in the chunk and, when possible, identify Toulmin elements for each claim.

Return strictly according to the structured schema. If a Toulmin element is not present, return an empty list for that element. For the warrant expression, return one of: "stated", "implied", or "none".

## Toulmin Definitions (concise)
- Claim: the assertion or conclusion to be established.
- Data/Grounds: evidence or facts that support the claim.
- Warrant: the assumption or principle that connects data to claim; it may be stated explicitly or implied implicitly.
- Qualifier: words/phrases indicating the strength/scope of the claim (e.g., "likely", "some", "many", "in most cases").
- Rebuttal: acknowledged exceptions or counter-arguments to the claim.
- Backing: additional support that justifies the warrant (e.g., theories, principles, authorities, or methodological reasons).

Reference: Purdue OWL - Toulmin Argument (for definitions and orientation): https://owl.purdue.edu/owl/general_writing/academic_writing/historical_perspectives_on_argumentation/toulmin_argument.html

{domain_context}

{audience_context}

## Important Instructions
- Focus only on content in the provided chunk when extracting claims and text evidence; use the full document only for context/clarification.
- Extract zero or more claims. If none are present, return an empty list.

**Substantiation Assessment:**
Set `needs_substantiation` to **False** for:
- Common knowledge widely accepted in the domain
- Basic definitions and established terminology
- Logical deductions from clearly stated premises
- General principles universally accepted in the field
- Simple factual statements available in reference sources

Set `needs_substantiation` to **True** for:
- Specific research findings or data claims
- Expert interpretations or opinions
- Recent developments or emerging concepts
- Comparative or evaluative assertions
- Complex causal explanations
- Contested or debatable statements

- For each identified claim:
  - "data": list specific evidence from the chunk that supports the claim (quoted or paraphrased).
  - "warrants": list the assumptions that link the data to the claim. If you infer a warrant from context, include it.
  - "warrant_expression":
    - "stated" if the warrant is explicitly articulated in the chunk,
    - "implied" if it is reasonably inferable but not directly stated,
    - "none" if no warrant can be identified.
  - "qualifiers": list hedging or scope-limiting language associated with the claim.
  - "rebuttals": list acknowledged exceptions or counter-arguments present in the chunk.
  - "backing": list any additional support for the warrant (e.g., principles, cited studies, theoretical reasons) if present.

## The full document that the chunk is a part of
```
{full_document}
```

## The paragraph of the original document that contains the chunk of text that we want to analyze
```
{paragraph}
```

## The chunk of text to analyze
```
{chunk}
```
"""
        )
    ),
    tools=[],
    mandatory_tools=[],
    output_schema=ToulminClaimResponse,
)
