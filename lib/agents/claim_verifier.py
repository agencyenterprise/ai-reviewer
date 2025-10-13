from enum import IntEnum

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from lib.config.llm import models
from lib.models.agent import Agent


class Severity(IntEnum):
    NO_ISSUE = 0
    NOT_ENOUGH_DATA = 1
    LOW_SEVERITY = 2
    MEDIUM_SEVERITY = 3
    HIGH_SEVERITY = 4


class ClaimSubstantiationResult(BaseModel):
    is_substantiated: bool = Field(
        description="A boolean value indicating whether the claim is substantiated by the supporting document(s) or not"
    )
    rationale: str = Field(
        description="A brief rationale for why you think the claim is substantiated or not substantiated by the cited supporting document(s)"
    )
    feedback: str = Field(
        description="A brief suggestion on how the issue can be resolved, e.g., by adding more supporting documents or by rephrasing the original chunk, etc. Return 'No changes needed' if there are no significant issues with the substantiation of the claim."
    )
    severity: Severity = Field(
        description=(
            "The severity of the substantiation issue with increasing numeric levels: "
            "0 = no issue, "
            "1 = not enough data to know for sure, "
            "2 = low severity issues, "
            "3 = medium severity issues, "
            "4 = high severity issues"
        )
    )
    severity_rationale: str = Field(
        description="A brief rationale for why you think the severity level is appropriate"
    )


class ClaimSubstantiationResultWithClaimIndex(ClaimSubstantiationResult):
    chunk_index: int
    claim_index: int


_claim_verifier_prompt = ChatPromptTemplate.from_template(
    """
# Task
You will be given a chunk of text from a document, a claim that is inferred from that chunk of text, and one or multiple supporting documents that are cited to support the claim.
Your task is to carefully read the supporting document(s) and determine wether the claim is supported by the supporting documents or not.
Return a rationale for why you think the claim is supported or not supported by the cited supporting document(s).

## Severity level definitions

For each claim, also output a numeric severity level based on the following definitions:

0 – No issue
The claim is well-substantiated and faithful to the source. No factual or interpretive drift.

1 – Not enough data
The supporting document(s) were not provided, or are inaccessible to confirm or deny the claim.

2 – Low severity issue
Minor inaccuracies or stylistic differences. The statement preserves the author’s meaning but could be worded more precisely or loses a small nuance. Acceptable in most contexts but worth polishing.

3 – Medium severity issue
Moderate distortion. The claim remains on the same topic but misstates scope, frequency, tone, or degree. Should be revised before publication.

4 – High severity issue
Major misrepresentation. The claim contradicts, reverses, or fabricates the source’s position, or adds strong unsupported language that would mislead a reader about the author’s intent. The claim uses numbers or metrics that are not supported by the source or are not clearly derived from the source. Must be corrected before publication.

## Other instructions

- Consider "low severity issues" as substantiated, so mark "is_substantiated" as true for these cases.
- Citations may appear in the same chunk of the text that the claim belongs to, or potentially in a later chunk of the paragraph. So you will also be given info for the paragraph and all the citations in the paragraph. Use your judgement to determine whether a reference is cited close enough to the actual claim of the text for readers to understand the author's intent that the citation is supporting that claim or not. For example, if all citations of an introduction paragraph are at the end of the paragraph, then it's likely that the citations are supporting all the claims in the whole paragraph together, rather than just supporting the last sentence/chunk of the paragraph.

{domain_context}

{audience_context}

## The original document from which we are substantiating claims within a chunk
```
{full_document}
```

## The paragraph of the original document that contains the chunk of text that we want to substantiate
```
{paragraph}
```

## The chunk of text from the original document that contains the claim to be substantiated
```
{chunk}
```

## The claim that is inferred from the chunk of text to be substantiated
{claim}

## The list of references cited in this chunk of text to support the claim and their associated supporting document (if any)
{cited_references}

## The list of references cited in outside of this chunk, but still in the same paragraph of text to support the claim and their associated supporting document (if any)
{cited_references_paragraph}

"""
)

claim_verifier_agent = Agent(
    name="Claim Verifier",
    description="Substantiate a claim based on a supporting document",
    model=models["gpt-5"],
    temperature=0.2,
    prompt=_claim_verifier_prompt,
    tools=[],
    mandatory_tools=[],
    output_schema=ClaimSubstantiationResult,
)
