"""RAG stress tests for challenging retrieval scenarios.

Tests RAG's ability to handle:
- Numerical precision (finding exact numbers in dense documents)
- Logical reasoning (majority = >50%, negation detection)
- Multi-source synthesis
- Subtle qualifiers (may vs will)
- Partial support detection
- Wrong citation detection
- Multi-hop reasoning
- Extended context requirements
"""

import asyncio
import pytest

from lib.agents.claim_verifier import ClaimSubstantiationResult
from lib.models.agent_test_case import AgentTestCase
from tests.conftest import TESTS_DIR, extract_paragraph_from_chunk, load_document
from tests.datasets.loader import load_dataset
from tests.llm.test_claim_verifier_rag import rag_claim_verifier_agent


def _build_cases():
    """Build RAG stress test cases."""
    dataset_path = str(TESTS_DIR / "datasets" / "rag_stress_tests.yaml")
    dataset = load_dataset(dataset_path)

    test_config = dataset.test_config
    strict_fields = test_config.strict_fields or set() if test_config else set()
    llm_fields = test_config.llm_fields or set() if test_config else set()

    cases: list[AgentTestCase] = []

    for test_case in dataset.items:
        main_doc = asyncio.run(load_document(test_case.input["main_document"]))
        supporting_docs = [
            asyncio.run(load_document(doc))
            for doc in test_case.input.get("supporting_documents", [])
        ]

        chunk = test_case.input["chunk"]
        claim_text = test_case.input["claim"]

        prompt_kwargs = {
            "main_doc": main_doc,
            "supporting_docs": supporting_docs,
            "chunk_text": chunk,
            "claim_text": claim_text,
            "domain": test_case.input.get("domain"),
            "target_audience": test_case.input.get("target_audience"),
        }

        cases.append(
            AgentTestCase(
                name=test_case.name,
                agent=rag_claim_verifier_agent,
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
async def test_rag_stress_cases(case: AgentTestCase):
    """Test RAG on challenging retrieval scenarios."""
    await case.run()
    eval_result = await case.compare_results()

    # Print diagnostics
    print(f"\n[{case.name}]")
    print(f"  Result: {'✓ PASS' if eval_result.passed else '✗ FAIL'}")
    if not eval_result.passed:
        print(f"  Reason: {eval_result.rationale}")

    assert eval_result.passed, f"{case.name}: {eval_result.rationale}"
