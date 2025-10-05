from enum import Enum

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from lib.config.llm import models
from lib.models.agent import Agent


class CommonKnowledgeType(Enum):
    WELL_ESTABLISHED_FACTS = "well_established_facts"
    BASIC_HISTORICAL_DATES_AND_EVENTS = "basic_historical_dates_and_events"
    FUNDAMENTAL_PRINCIPLES_AND_THEORIES = "fundamental_principles_and_theories"
    GENERAL_STATISTICAL_TRENDS = "general_statistical_trends"
    STANDARD_DEFINITIONS_AND_TERMINOLOGY = "standard_definitions_and_terminology"
    BASIC_GEOGRAPHIC_DEMOGRAPHIC_OR_INSTITUTIONAL_FACTS = (
        "basic_geographic_demographic_or_institutional_facts"
    )
    OTHER = "other"


class ClaimType(Enum):
    POLICY = "policy"
    RESEARCH = "research"
    STATISTICAL_DATA = "statistical_data"
    EXPERT_OPINION = "expert_opinion"
    NEWS_REPORT = "news_report"
    OTHER = "other"


class ClaimCommonKnowledgeResult(BaseModel):
    is_common_knowledge: bool = Field(
        default=False,
        description="A boolean value that is True if the claim represents common knowledge in the domain that typically doesn't require substantiation, and False otherwise",
    )
    claim_types: list[ClaimType] = Field(
        default=[],
        description="The type(s) of the claim",
    )
    common_knowledge_types: list[CommonKnowledgeType] = Field(
        default=[],
        description=("The type(s) of common knowledge that the claim represents"),
    )
    common_knowledge_rationale: str = Field(
        default="",
        description="A brief explanation for why this claim is or is not considered common knowledge in the specified domain and context",
    )
    needs_substantiation: bool = Field(
        description="A boolean value indicating whether the claim needs to be substantiated. "
    )
    substantiation_rationale: str = Field(
        default="",
        description="A brief explanation for why this claim needs to or does not need to be substantiated by references/evidence",
    )


class ClaimCommonKnowledgeResultWithClaimIndex(ClaimCommonKnowledgeResult):
    chunk_index: int
    claim_index: int


_claim_common_knowledge_checker_prompt = ChatPromptTemplate.from_template(
    """
# Task
You will be given a chunk of text from a document and a claim that is inferred from that chunk of text. Your task is to determine if this claim represents common knowledge in the domain or not, and whether the claim can be considered common knowledge, and whether the claim needs to be substantiated by references/evidence or not.

Return:
- is_common_knowledge: A boolean value indicating whether the claim represents common knowledge in the domain
  - Make specific quantitative assertions ("most", "majority", "significant portion") without supporting data
  - Use vague qualifiers that need clarification ("for the most part", "largely", "typically")
  - Could benefit from more precise language or supporting evidence for the intended audience
- common_knowledge_types: A list of the type(s) of common knowledge that the claim represents (if any)
- claim_types: A list of the type(s) of the claim
- common_knowledge_rationale: A brief explanation for your common knowledge determination - explain why this claim is or is not considered common knowledge given the specified domain and target audience context.
- needs_substantiation: A boolean value indicating whether the claim needs to be substantiated by references/evidence
- substantiation_rationale: A brief explanation for why this claim needs to or does not need to be substantiated by references/evidence

**Important guidance on substantiation needs:**
Set `needs_substantiation` to **False** for:
- Well-established facts widely known in the domain
- Basic definitions and terminology
- Logical deductions that follow clearly from stated premises
- General principles universally accepted in the field
- Simple factual statements readily available in reference sources
- Common knowledge that domain experts would not question

Set `needs_substantiation` to **True** for:
- If there are any references cited in this chunk of text, then regardless of whether we think the claim is common knowledge or not, then the claim MUST be substantiated
- Specific research findings or statistical claims
- Expert opinions or interpretations
- Recent developments or emerging trends
- Comparative analyses or evaluative statements
- Causal claims or complex explanatory mechanisms
- Contested or debatable assertions

{domain_context}

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
7. **Statements describing the structure or scope of the work itself** that report on the authors’ own methodology, goals, or organization rather than asserting external facts.

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
"""
)

claim_common_knowledge_checker_agent = Agent(
    name="Claim Common Knowledge Checker",
    description="Check if a claim represents common knowledge in the domain",
    model=models["gpt-5"],
    prompt=_claim_common_knowledge_checker_prompt,
    tools=[],
    mandatory_tools=[],
    output_schema=ClaimCommonKnowledgeResult,
)
