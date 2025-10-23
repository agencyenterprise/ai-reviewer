# testing the categorization of claims

# %%
"""

Categorizes claims from research documents into predefined categories.

Each claim is analyzed to determine:
- Category (using a 6-category taxonomy)
- Rationale for the categorization
- Whether external verification is needed

The agent uses structured outputs via Pydantic models to ensure consistent
and validated responses that can be reliably processed downstream.

The categories are:
- Established/reported knowledge
- Methodology/procedural
- Empirical/analytical results
- Inferential/interpretive claims
- Meta/structural/evaluative
- Other

"""
from __future__ import annotations
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from lib.models.agent import DEFAULT_LLM_TIMEOUT, Agent, AgentProtocol

from enum import Enum

from lib.config.llm import models


from pydantic import BaseModel, Field, field_validator

# =========================
#  Pydantic data contracts
# =========================


class ClaimCategory(str, Enum):
    ESTABLISHED = "established_reported_knowledge"
    METHODOLOGY = "methodology_procedural"
    RESULTS = "empirical_analytical_results"
    INTERPRETATION = "inferential_interpretive_claims"
    META = "meta_structural_evaluative"
    OTHER = "other"


class ClaimCategorizationResponse(BaseModel):
    claim: str = Field(description="Exact claim text as analyzed.")
    claim_category: ClaimCategory = Field(description="Assigned category.")
    rationale: str = Field(description="One-line reason for the category assignment.")
    needs_external_verification: bool = Field(
        description=(
            "True if: (a) the sentence contains a citation, OR (b) it asserts reported/established "
            "knowledge that originates outside the current document/analysis and would typically "
            "require an external source. False for purely internal methods/results/structure."
        ),
    )


class ClaimCategorizationResponseWithClaimIndex(ClaimCategorizationResponse):
    chunk_index: int
    claim_index: int


_claim_categorizer_prompt = ChatPromptTemplate.from_template(
    """
You are an expert claim categorizer. Your task is to tag the specific claim in a passage
with ONE of SIX categories and to determine if it needs EXTERNAL VERIFICATION.

CATEGORIES WITH EXAMPLES:

1. **Established / Reported Knowledge** -> Requires citations most often

   - Purpose: to anchor statements in prior verified work, including background theory, prior empirical results, standard parameter values, or definitions not universally accepted.
   - Typical content: Contains background facts, prior research findings, textbook principles, or definitions.
   - Examples:
       • "Protein folding is governed by the hydrophobic effect (Kauzmann, 1959)."
       • "Graphene has a Young's modulus of ~1 TPa (Lee et al., 2008)."
       • "Previous studies have shown that X causes Y (Smith et al., 2021)."
       • "According to prior studies, neural networks outperform linear models on vision tasks."
   - Rule of Thumb for citations:
        - If the knowledge did not originate in this paper and is not universally accepted, cite it.
   - Citation exemptions:
        - If the knowledge is universally accepted in the domain, then it does not need to be cited (The chemical composition of water is H2O; The United States is a country; The speed of light is 299,792,458 meters per second)

2. **Methodology / Procedural** -> Often requires citations

   - Purpose: to describe how something was done — datasets, methods, variables, preprocessing,
     analytic choices, or limitations.
   - Typical content: description of algorithms, methods, instruments, model architectures, or data sources. Contains phrases like "used" "followed" "took" "collected" "preprocessed" "analyzed" "validated." Includes adjustments, control variables, data processing, or validation steps.
   - Examples:
       • "We used a logistic regression with L2 regularization."
       • "We used the Adam optimizer (Kingma & Ba, 2014)."
       • "The dataset was taken from the UCI repository (Dua & Graff, 2019)."
       • "Survey data were collected between 2019-2020 using random sampling."
       • "Following the approach of Zhao et al. (2022), we fine-tuned BERT for classification."
   - Rule of Thumb for citations:
        - If the method, algorithm, dataset, or software package used in the sentence did not originate in this paper and is not universally accepted, then it requires a citation.
   - Citation exemptions:
        - Citations are not required for methodologies that are universally accepted in the domain (e.g., stochastic gradient descent in DL and AI; bag of words in NLP; etc.)

3. **Empirical / Analytical Results** -> Usually does not require citations

   - Purpose: to present new findings or quantitative results generated within the current work.
   - Typical content: measured values, error rates, or discovered patterns. Contains phrases like "improved by" "reached equilibrium in" "found a strong correlation between"
   - Examples:
       • "Accuracy improved by 12 percentage points over baseline."
       • "The reaction reached equilibrium in 30 seconds."
       • "We found a strong correlation between the two variables."
   - Rule of Thumb for citations:
        - Results obtained from the current work should not require a citation unless these results are compared to prior work or external theory (e.g., "Our accuracy exceeds the 89 percent reported by Li et al., 2023.")  require a citation for the baseline.

4. **Inferential / Interpretive Claims** -> Occasionally requires citations

   - Purpose: To draw conclusions, interpretations, or hypotheses from the results of the current work, prior theory, or references
   - Typical content: Causality, mechanism, theoretical explanation, or significance interpretation. Contains phrases like "suggests" "implies" "may indicate" "supports" "implies" "suggests" "may indicate" "supports"
   - Examples:
       • "This trend suggests that diffusion limits the reaction rate."
       • "The findings imply that public trust increases with transparency."
       • "This trend supports the hypothesis that diffusion limits the reaction rate (Anderson et al., 2019)."
       • "We argue that the observed pattern indicates a causal relationship."
       • "Consistent with prior models of turbulent mixing (Kolmogorov, 1941)."
   - Includes explanations, causal reasoning, and theoretical implications.

5. **Meta / Structural / Evaluative** -> Rarely requires citations

   - Purpose: to manage discourse, describe organization, express novelty or significance.
   - Typical content: section transitions, claims of contribution, limitation statements. Contains phrases like "in the next section" "in the following section"
   - Examples:
       • "In the next section we discuss limitations."
       • "This study represents a significant improvement over previous work."
   - Includes signposting or self-referential commentary.
   - Rule of Thumb for citations:
        - Usually no citation required, except when explicitly comparing to prior studies, external theory, or previous work.

6. **Other**
   - Only use if none of the above categories fit.


---

NEEDS EXTERNAL VERIFICATION (boolean):
- Set to TRUE if:
    (a) the sentence includes a citation marker (e.g., [12], (Smith, 2022), superscripts)
        → automatically requires verification, OR
    (b) it asserts or references reported or established knowledge from outside this document or a claim that is not specific to the current document
        (i.e., would require external source confirmation).
- Set to FALSE for:
    - Methods, data, results, or interpretations specific to this document
    - Structural or organizational sentences

---

Return one JSON object matching the schema exactly. Each sentence must
have exactly one category and one-line rationale.

## Domain Context
{domain_context}

## Audience Context
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

## The claim that is inferred from the chunk of text. This is the claim that we want to categorize.
```
{claim}
```
"""
)


class ClaimCategorizerAgent(AgentProtocol):
    name: str = "Claim Categorizer"
    description: str = "Categorize a claim into one of the six categories"

    def __init__(self):
        self.llm = init_chat_model(
            models["gpt-5"],
            temperature=0.2,
            timeout=DEFAULT_LLM_TIMEOUT,
        ).with_structured_output(ClaimCategorizationResponse)

    async def ainvoke(
        self, prompt_kwargs: dict, config: RunnableConfig = None
    ) -> ClaimCategorizationResponse:
        messages = _claim_categorizer_prompt.format_messages(**prompt_kwargs)
        return await self.llm.ainvoke(messages, config=config)


claim_categorizer_agent = ClaimCategorizerAgent()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    from lib.models.react_agent.agent_runner import _ensure_structured_output

    nest_asyncio.apply()
    # Test cases with expected vs inferred categorizations
    test_cases = [
        {
            "domain_context": "Military personnel management and technology",
            "audience_context": "Military leadership and HR professionals",
            "full_document": """In recent years, RAND Project AIR FORCE (PAF) has supported the U.S. Air Force's efforts to enhance its talent management practices through technology investments (Schulker et al., 2022; Snyder, 2022; Yeung et al., 2022). These projects demonstrate that leveraging emerging technology can transform the USAF's talent management system. Beyond conceptual work, PAF developed a prototype tool, Personnel Records Scoring System (PReSS), and tested it with select DTs. In this report, we describe improvements to PReSS and an expansion to enlisted personnel.""",
            "paragraph": """In recent years, RAND Project AIR FORCE (PAF) has supported the U.S. Air Force's efforts to enhance its talent management practices through technology investments (Schulker et al., 2022; Snyder, 2022; Yeung et al., 2022). These projects demonstrate that leveraging emerging technology can transform the USAF's talent management system.""",
            "chunk": chunk,
            "claim": claim,
            "expected_category": expected,
            "expected_needs_verification": needs_verification,
        }
        for chunk, claim, expected, needs_verification in [
            # Test case 1: Established knowledge requiring citation since not universally accepted
            (
                "RAND Project AIR FORCE (PAF) has supported the U.S. Air Force's efforts and there is a past history of developing technology to support talent management (Schulker et al., 2022; Snyder, 2022; Yeung et al., 2022)",
                "RAND Project AIR FORCE (PAF) has supported the U.S. Air Force's efforts and there is a past history of developing technology to support talent management (Schulker et al., 2022; Snyder, 2022; Yeung et al., 2022)",
                ClaimCategory.ESTABLISHED,
                True,
            ),
            # Test case 2: Methodology/procedural - description of what was done, original to this work
            (
                "PAF developed a prototype tool, Personnel Records Scoring System (PReSS) by leveraging existing technology and data sources",
                "PAF developed a prototype tool, Personnel Records Scoring System (PReSS) by leveraging existing technology and data sources",
                ClaimCategory.METHODOLOGY,
                False,
            ),
            # Test case 3: Empirical/analytical results (original findings presented by authors), no citation needed
            (
                "PAF tested PReSS with select DTs and found that it was 20 percent more effective in improving the USAF's talent management system than the baseline",
                "PAF tested PReSS with select DTs and found that it was 20 percent more effective in improving the USAF's talent management system than the baseline",
                ClaimCategory.RESULTS,
                False,
            ),
            # Test case 4: Inferential/interpretive (drawing a conclusion from methods/results), occasionally requires citation but not here as it's a direct inference
            (
                "These projects demonstrate that leveraging technology can transform talent management",
                "These projects demonstrate that leveraging technology can transform talent management",
                ClaimCategory.INTERPRETATION,
                False,
            ),
            # Test case 5: Meta/structural statement (about document structure/content), rarely requires citation
            (
                "In this report, we describe improvements to PReSS",
                "In this report, we describe improvements to PReSS",
                ClaimCategory.META,
                False,
            ),
            # Test case 6: Established/reported knowledge with explicit citations (external knowledge), always needs verification
            (
                "It has been shown that technology investments (Schulker et al., 2022; Snyder, 2022; Yeung et al., 2022) can transform the USAF's talent management system",
                "It has been shown that technology investments (Schulker et al., 2022; Snyder, 2022; Yeung et al., 2022) can transform the USAF's talent management system",
                ClaimCategory.ESTABLISHED,
                True,
            ),
            # Test case 7: Methodology detail (testing process described, original to authors)
            (
                "As additional tests, the method was extended to an eigenvalue analysis in order to explore whether additional factors are important in predicting the effectiveness of the PReSS system",
                "As additional tests, the method was extended to an eigenvalue analysis in order to explore whether additional factors are important in predicting the effectiveness of the PReSS system",
                ClaimCategory.METHODOLOGY,
                False,
            ),
            # Test case 8: Empirical result (new information generated within the work, no comparison to external findings)
            (
                "The eigenvalue analysis found that the additional factors were not important in predicting the effectiveness of the PReSS system",
                "The eigenvalue analysis found that the additional factors were not important in predicting the effectiveness of the PReSS system",
                ClaimCategory.RESULTS,
                False,
            ),
            # Test case 9: Inferential claim making broader theoretical conclusion, cites no external work
            (
                "This suggests that advanced mathematical methods can be used to predict the effectiveness of the PReSS system, but they don't appear to be necessary",
                "This suggests that advanced mathematical methods can be used to predict the effectiveness of the PReSS system, but they don't appear to be necessary",
                ClaimCategory.INTERPRETATION,
                False,
            ),
            # Test case 10: Use 'other' only if none above fit; this is a catch-all for edge or ambiguous statements, still requires verification if asserted as fact
            (
                "National Institute of Standards and Technology (NIST); Pentagoin (2022); etc.",
                "National Institute of Standards and Technology (NIST); Pentagoin (2022); etc.",
                ClaimCategory.OTHER,
                True,
            ),
        ]
    ]

    # Run tests and compare results
    for i, test_case in enumerate(test_cases, 1):
        response = asyncio.run(claim_categorizer_agent.ainvoke(test_case))

        print(f"\nTest Case {i}:")
        print(f"Claim: {test_case['claim']}")
        print(f"Expected Category: {test_case['expected_category']}")
        print(f"Inferred Category: {response.claim_category}")
        print(
            f"Expected Needs Verification: {test_case['expected_needs_verification']}"
        )
        print(f"Inferred Needs Verification: {response.needs_external_verification}")
        print(
            f"Match: {test_case['expected_category'] == response.claim_category and test_case['expected_needs_verification'] == response.needs_external_verification}"
        )
