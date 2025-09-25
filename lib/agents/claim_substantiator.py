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
    is_common_knowledge: bool = Field(
        default=False,
        description="Whether this claim represents common knowledge in the domain that typically doesn't require substantiation",
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

**Important**: Also determine if this claim represents common knowledge in the domain. Set `is_common_knowledge` to true if the claim falls under the common knowledge categories defined below, even if it lacks direct citation. Claims marked as common knowledge should typically have severity 0 or 1.

You MUST include both the "severity" and "is_common_knowledge" fields in your output.

## Document-Specific Context
### Domain: 
{domain_context}

### Target Audience:
{audience_context}

## General Evaluation Framework

### Common Knowledge vs. Claims Requiring Substantiation:

#### **Common Knowledge (Generally does NOT require substantiation):**
1. **Well-established facts** widely accepted in the field and appearing across multiple authoritative sources
2. **Basic historical dates and events** that are undisputed (e.g., major wars, founding dates)
3. **Fundamental principles** or theories in the domain that are universally accepted by practitioners
4. **General statistical trends** that are widely reported and uncontroversial
5. **Standard definitions** and terminology established in the field
6. **Basic geographic, demographic, or institutional facts** readily available in reference sources

#### **Claims Requiring Substantiation:**
1. **Specific research findings** or data points from studies, surveys, or analyses
2. **Expert opinions or interpretations** not universally held in the field
3. **Recent developments or trends** not yet widely established
4. **Comparative analyses or rankings** between entities, programs, or policies
5. **Causal relationships** or explanatory mechanisms
6. **Quantitative claims** with specific numbers, percentages, or measurements
7. **Policy recommendations or normative statements** about what should be done
8. **Contested or debatable assertions** where reasonable experts might disagree

#### **Domain-Specific Considerations:**
- What constitutes "common knowledge" varies significantly by field and audience expertise
- When in doubt about whether something is common knowledge, err to needs to check with the target audience
- Consider the **target audience's familiarity** with the domain when determining if something is common knowledge

### Evidence Quality Hierarchy (highest to lowest):
- Primary research and original data analysis
- Peer-reviewed academic publications
- Government and institutional reports from credible organizations
- Expert testimony and professional opinions
- News reports and secondary sources
- Non-peer-reviewed or self-published material

### Common Audience Expectations:
- **Policy Makers**: Need clear, actionable insights backed by authoritative sources
- **Researchers**: Expect rigorous methodology and peer-reviewed citations
- **Academic Community**: Requires proper attribution and scholarly standards
- **Government Officials**: Need verified information for decision-making

### Substantiation Standards by Claim Type:
- **For Policy Claims**: Verify against official sources, regulations, and authoritative policy documents
- **For Research Findings**: Ensure peer-review status, methodology disclosure, and replicability
- **For Statistical Data**: Confirm data sources, collection methods, and sample representativeness
- **For Expert Opinions**: Validate credentials, institutional affiliation, and relevance to topic

**Important**: Adjust your evaluation criteria based on the specific domain and target audience provided above. When claims lack sufficient substantiation for the intended audience and domain, prioritize higher severity levels.

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
