"""Basic claim substantiation tests."""

import asyncio
import pytest

from lib.agents.claim_substantiator import (
    ClaimSubstantiationResult,
    claim_substantiator_agent,
)
from lib.agents.formatting_utils import (
    format_audience_context,
    format_domain_context,
    format_supporting_documents_prompt_section,
)
from lib.models.agent_test_case import AgentTestCase
from tests.conftest import TESTS_DIR, extract_paragraph_from_chunk, load_document
from tests.datasets.loader import load_dataset


def _build_cases():
    """Build test cases from basic dataset."""

    dataset_path = str(TESTS_DIR / "datasets" / "claim_substantiator.yaml")
    dataset = load_dataset(dataset_path)

    # Get test configuration from dataset, with defaults if not present
    test_config = dataset.test_config
    if test_config:
        strict_fields = test_config.strict_fields or set()
        llm_fields = test_config.llm_fields or set()

    cases: list[AgentTestCase] = []

    for test_case in dataset.items:
        # Load main document
        main_doc = asyncio.run(load_document(test_case.input["main_document"]))

        # Build supporting documents block if provided
        supporting_docs = [
            asyncio.run(load_document(supporting_doc))
            for supporting_doc in test_case.input.get("supporting_documents", [])
        ]

        # Extract inputs
        chunk = test_case.input["chunk"]
        claim_text = test_case.input["claim"]
        domain = test_case.input.get("domain")
        target_audience = test_case.input.get("target_audience")
        paragraph = extract_paragraph_from_chunk(main_doc.markdown, chunk)

        cited_references = ""
        for supporting_doc in supporting_docs:
            cited_references += format_supporting_documents_prompt_section(
                supporting_doc
            )
            cited_references += "\n\n"

        # Build prompt kwargs
        prompt_kwargs = {
            "full_document": main_doc.markdown,
            "paragraph": paragraph,
            "chunk": chunk,
            "claim": claim_text,
            "cited_references": cited_references,
            "cited_references_paragraph": "",
            "domain_context": format_domain_context(domain),
            "audience_context": format_audience_context(target_audience),
        }

        cases.append(
            AgentTestCase(
                name=test_case.name,
                agent=claim_substantiator_agent,
                response_model=ClaimSubstantiationResult,
                prompt_kwargs=prompt_kwargs,
                expected_dict=test_case.expected_output,
                strict_fields=strict_fields,
                llm_fields=llm_fields,
            )
        )

    return cases


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _build_cases(), ids=lambda case: case.name)
async def test_claim_substantiator(case):
    """Test basic claim substantiation cases."""
    await case.run()
    eval_result = await case.compare_results()

    assert eval_result.passed, f"{case.name}: {eval_result.rationale}"
