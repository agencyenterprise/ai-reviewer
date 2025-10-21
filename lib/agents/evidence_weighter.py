from enum import Enum
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from lib.models.agent import Agent
from lib.config.llm import models
from lib.agents.claim_verifier import EvidenceAlignmentLevel
from lib.agents.live_literature_review import (
    QualityLevel,
    ClaimReferenceFactors,
)


# applies to the claim
class EvidenceAlignmentLevel(str, Enum):
    UNVERIFIABLE = "unverifiable"
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"


class EvidenceWeighterRecommendedAction(str, Enum):
    UPDATE_CLAIM = "update_claim"  # claim is either no longer true and needs to be updated or it should be qualified given the newer sources
    ADD_CITATION = "add_citation"  # claim can remain as is,  but additional citations prove more influential
    NO_CHANGE = "no_update_needed"  # claim does not need to be updated


class EvidenceWeighterResponse(BaseModel):
    newer_references: list[ClaimReferenceFactors] = Field(
        description="Newer references found from the literature review report"
    )
    newer_references_alignment: EvidenceAlignmentLevel = Field(
        description="Evidence alignment of the newer references: unverifiable, supported, partially_supported, or unsupported"
    )
    claim_update_action: EvidenceWeighterRecommendedAction = Field(
        description="Recommended action for the claim: update_claim, add_citation, or no_change"
    )
    rationale: str = Field(description="Explanation of the claim update")
    confidence_level: QualityLevel = Field(
        description="Confidence level in the claim update: high, medium, or low"
    )


class EvidenceWeighterResponseWithClaimIndex(EvidenceWeighterResponse):
    chunk_index: int
    claim_index: int


_evidence_weighter_agent_prompt = ChatPromptTemplate.from_template(
    """
# Role
You are an expert research evidence analyst specializing in evaluating the strength, quality, and direction of sources that are relevant to claims in research document. 

# Goal
You will be given a new literature review report that contains the newer sources that have been found recently for a claim. Analyze this collection of newer sources to determine the overall evidence direction and strength for a specific claim, considering source quality, methodology, and potential biases. Importantly state whether the newer sources override the older ones in supporting, contextualizing, or conflicting with the claim. 

# Analysis Framework

From the existing sources that are cited to support the claim and the newer sources that have been found recently for the claim, analyze the sources to determine the overall evidence direction and strength for a specific claim, considering source quality, methodology, and potential biases. Importantly state whether the newer sources override the existing sources in supporting, contextualizing, or conflicting with the claim.

## Claim Classification Guidelines

For each claim provide the following:
- evidence factors
- evidence alignment 
- recommended action
- confidence in recommended action
- rationale for the recommended action

### Evidence Alignment
- **Unverifiable**: The supporting document(s) were not provided, or are inaccessible to confirm or deny the claim.
- **Supported**: The claim is substantiated by the cited material. The reference clearly provides evidence or reasoning that matches both the claim’s factual scope and its evaluative tone.
- **Partially Supported**: The citation provides related evidence but doesn’t fully substantiate the claim. It may support only part of the statement or use weaker phrasing than the claim implies. The mismatch usually involves scope, frequency, or tone rather than outright contradiction.
- **Unsupported**: The cited material does not contain evidence for the claim or the claim contradicts or reverses the source’s position, or adds strong unsupported language that would mislead a reader about the author’s intent. The claim may also use numbers or metrics that are not supported by the source or are not clearly derived from the source.

### Recommended Action
- **Update Claim**: The claim is either no longer true and needs to be updated or it should be qualified given the newer sources
- **Add Citation**: The claim can remain as is,  but additional citations prove more influential
- **No Change**: The claim does not need to be updated

### Confidence in Recommended Action
- **High**: There are multiple high-quality sources with consistent findings and clear consensus
- **Medium**: There are some quality sources but with some inconsistencies or limited evidence
- **Low**: There is limited or conflicting evidence from quality sources, or mostly low-quality sources or the evidence is unverifiable

### Rationale for the Recommended Action
- Brief explanation for why the recommended action is appropriate given the evidence alignment and confidence in the recommended action


General Guidelines for Processing
- Use the full document and paragraph context to understand the claim's role and importance.
- If the claim is essential to the argument of the paragraph or document and thus consistency between the claim and the evidence is important. If the evidence is not consistent with the claim, then the claim needs to be updated. If the evidence is consistent with the claim, then the claim can remain as is. If the evidence is not consistent with the claim, then the claim needs to be updated.
- Don't simply use the title of the source to determine the evidence alignment. Look at the content of the source to determine the evidence alignment.
- Don't simply count the number of supporting sources to determine the evidence alignment. Look at the content and quality of the sources to determine the evidence alignment.

# Output Requirements
- Provide specific rationale for each quality factor level (high/medium/low)
- Identify any methodological concerns or limitations
- Note potential biases in the evidence base
- Explain the reasoning behind the overall evidence direction
- Suggest areas where additional evidence might be needed

Use the following markdown format of sections:

Here are the contextual details:

## Document Context
**Domain**: {domain_context}
**Target Audience**: {audience_context}

## The full document that contains the claim
```
{full_document}
```

## The list of references already cited in this chunk of text to support the claim and their associated supporting document (if any)
{cited_references}

## The list of references already cited in outside of this chunk, but still in the same paragraph of text to support the claim and their associated supporting document (if any)
{cited_references_paragraph}

## The paragraph containing the claim
```
{paragraph}
```

## The specific chunk containing the claim
```
{chunk}
```

## The original claim being analyzed
```
{claim}
```

## The newer references found from the literature review report
```
{newer_references}
```

## Summary of the references landscape
```
{evidence_summary}
```
"""
)

evidence_weighter_agent = Agent(
    name="Evidence Weighting Analyst",
    description="Analyze and weight evidence from multiple sources to determine overall direction and strength",
    model=models["gpt-5"],
    use_responses_api=True,
    use_react_agent=False,
    use_direct_llm_client=True,
    use_background_mode=False,
    prompt=_evidence_weighter_agent_prompt,
    tools=[],
    mandatory_tools=[],
    output_schema=EvidenceWeighterResponse,
)
