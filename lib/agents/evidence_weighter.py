from enum import Enum

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langfuse.openai import AsyncOpenAI
from pydantic import BaseModel, Field

from lib.agents.live_literature_review import ClaimReferenceFactors, QualityLevel
from lib.config.llm import models
from lib.models.agent import DEFAULT_LLM_TIMEOUT, AgentProtocol
from lib.models.llm import ensure_structured_output_response


# applies to the claim
class ReferenceAlignmentLevel(str, Enum):
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
    newer_references_alignment: ReferenceAlignmentLevel = Field(
        description="Evidence alignment of the newer references: unverifiable, supported, partially_supported, or unsupported"
    )
    claim_update_action: EvidenceWeighterRecommendedAction = Field(
        description="Recommended action for the claim: update_claim, add_citation, or no_change"
    )
    rationale: str = Field(
        description="Explanation of the rationale for the claim update action in a maximum of TWO sentences."
    )
    confidence_level: QualityLevel = Field(
        description="Confidence level in the claim update: high, medium, or low"
    )
    rewritten_claim: str = Field(
        description="The rewritten claim that is more clear and accurate according to the recommended action and taking the newer sources into account."
    )


class EvidenceWeighterResponseWithClaimIndex(EvidenceWeighterResponse):
    chunk_index: int
    claim_index: int


_evidence_weighter_agent_prompt = PromptTemplate.from_template(
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

### Claim Update Action
- **Update Claim**: The claim is either no longer true and needs to be updated to state the correct information or the claim is partially true and should be qualified given the newer sources
- **Add Citation**: The claim can remain as is,  but additional citations prove more influential
- **No Change**: The claim does not need to be updated

### Confidence in Claim Update Action
- **High**: There are multiple high-quality sources with consistent findings and clear consensus
- **Medium**: There are some quality sources but with some inconsistencies or limited evidence
- **Low**: There is limited or conflicting evidence from quality sources, or mostly low-quality sources or the evidence is unverifiable

### Rationale for the Claim Update Action
- Brief explanation for why the recommended action is appropriate given the evidence alignment and confidence in the recommended action. In a maximum of TWO sentences.

### Rewritten Claim
- Rewrite the claim according to the recommended action and taking the newer sources into account.

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


class EvidenceWeighterAgent(AgentProtocol):
    name: str = "Evidence Weighter"
    description: str = (
        "Analyze and weight evidence from multiple sources to determine overall direction and strength"
    )

    def __init__(self):
        # TODO: allow switching for Azure OpenAI
        self.client = AsyncOpenAI(timeout=DEFAULT_LLM_TIMEOUT)

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ) -> EvidenceWeighterResponse:
        prompt = _evidence_weighter_agent_prompt.invoke(prompt_kwargs)
        input = [{"role": "user", "content": prompt.text}]

        response = await self.client.responses.parse(
            model=models["gpt-5"].name,
            tools=[{"type": "web_search"}],
            max_tool_calls=20,
            # reasoning={
            #     "effort": "low",  # "minimal", "low", "medium", "high"
            #     "summary": "auto",
            # },
            text_format=EvidenceWeighterResponse,
            input=input,
        )

        return ensure_structured_output_response(response, EvidenceWeighterResponse)


evidence_weighter_agent = EvidenceWeighterAgent()
