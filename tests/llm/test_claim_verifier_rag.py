"""RAG-based claim substantiation tests.

This test suite uses RAG (Retrieval Augmented Generation) for claim verification,
which retrieves relevant passages from supporting documents instead of passing
full documents in the prompt. Results can be compared with test_claim_verifier.py
to evaluate the effectiveness of the RAG approach.
"""

import asyncio
import pytest

from lib.agents.claim_extractor import Claim, ClaimResponse
from lib.agents.claim_verifier import ClaimSubstantiationResult
from lib.models.field_comparator import FieldComparator
from lib.services.file import FileDocument
from lib.workflows.claim_substantiation.nodes.index_supporting_documents import (
    index_supporting_documents,
)
from lib.workflows.claim_substantiation.nodes.verify_claims_rag import (
    _verify_chunk_claims_rag,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
    SubstantiationWorkflowConfig,
)
from tests.conftest import TESTS_DIR, extract_paragraph_from_chunk, load_document
from tests.datasets.loader import load_dataset


async def _run_rag_verification(
    main_doc: FileDocument,
    supporting_docs: list[FileDocument],
    chunk_text: str,
    claim_text: str,
    domain: str | None,
    target_audience: str | None,
) -> ClaimSubstantiationResult:
    """Run RAG-based claim verification for a single claim."""

    # Create workflow config with RAG enabled
    config = SubstantiationWorkflowConfig(
        use_rag=True,
        domain=domain,
        target_audience=target_audience,
        session_id=f"test_rag_{id(main_doc)}",
    )

    # Extract paragraph from chunk
    paragraph = extract_paragraph_from_chunk(main_doc.markdown, chunk_text)

    # Find paragraph index (simplified - assumes chunk is at start of paragraph)
    paragraphs = main_doc.markdown.split("\n\n")
    paragraph_index = 0
    for i, para in enumerate(paragraphs):
        if chunk_text in para:
            paragraph_index = i
            break

    # Create a DocumentChunk with the claim
    chunk = DocumentChunk(
        chunk_index=0,
        paragraph_index=paragraph_index,
        content=chunk_text,
        claims=ClaimResponse(
            claims=[
                Claim(
                    claim=claim_text,
                    text=chunk_text,
                    rationale="Test claim for RAG verification",
                )
            ],
            rationale="Test claims extracted for RAG verification",
        ),
        citations=None,  # Will be populated if needed
        claim_common_knowledge_results=[],  # Empty means needs substantiation
    )

    # Create initial state
    state = ClaimSubstantiatorState(
        file=main_doc,
        supporting_files=supporting_docs,
        config=config,
        chunks=[chunk],
    )

    # Index supporting documents
    await index_supporting_documents(state)

    # Run RAG verification on the chunk
    verified_chunk = await _verify_chunk_claims_rag(state, chunk)

    # Extract the result
    if verified_chunk.substantiations:
        return verified_chunk.substantiations[0]
    else:
        raise ValueError("No substantiation results returned")


def _build_cases():
    """Build test cases from dataset using RAG verification."""

    dataset_path = str(TESTS_DIR / "datasets" / "claim_verifier.yaml")
    dataset = load_dataset(dataset_path)

    # Get test configuration from dataset
    test_config = dataset.test_config
    strict_fields = set()
    llm_fields = set()
    if test_config:
        strict_fields = test_config.strict_fields or set()
        llm_fields = test_config.llm_fields or set()

    cases = []

    for test_case in dataset.items:
        # Load main document
        main_doc = asyncio.run(load_document(test_case.input["main_document"]))

        # Load supporting documents
        supporting_docs = [
            asyncio.run(load_document(supporting_doc))
            for supporting_doc in test_case.input.get("supporting_documents", [])
        ]

        # Extract inputs
        chunk = test_case.input["chunk"]
        claim_text = test_case.input["claim"]
        domain = test_case.input.get("domain")
        target_audience = test_case.input.get("target_audience")

        cases.append(
            {
                "name": f"{test_case.name}_rag",
                "main_doc": main_doc,
                "supporting_docs": supporting_docs,
                "chunk": chunk,
                "claim_text": claim_text,
                "domain": domain,
                "target_audience": target_audience,
                "expected_output": test_case.expected_output,
                "strict_fields": strict_fields,
                "llm_fields": llm_fields,
            }
        )

    return cases


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _build_cases(), ids=lambda case: case["name"])
async def test_claim_verifier_rag(case):
    """Test RAG-based claim substantiation cases.

    These tests use the same dataset and evaluation criteria as test_claim_verifier.py,
    allowing for direct comparison between the full-text and RAG approaches.
    """
    # Run RAG verification
    result = await _run_rag_verification(
        main_doc=case["main_doc"],
        supporting_docs=case["supporting_docs"],
        chunk_text=case["chunk"],
        claim_text=case["claim_text"],
        domain=case["domain"],
        target_audience=case["target_audience"],
    )

    # Parse expected and actual results
    expected = ClaimSubstantiationResult.model_validate(case["expected_output"])

    # Compare strict fields
    if case["strict_fields"]:
        comparator = FieldComparator(case["strict_fields"], set())
        field_comparisons = comparator.compare_fields(
            expected, result, comparison_type="strict"
        )

        for fc in field_comparisons:
            assert (
                fc.passed
            ), f"{case['name']} - Strict field '{fc.field_path}' failed: {fc.rationale}"

    # For LLM fields, we'll do a simple check (you can enhance this with LLM evaluation later)
    if case["llm_fields"]:
        # For now, just check that the fields exist
        for field in case["llm_fields"]:
            assert hasattr(
                result, field
            ), f"{case['name']} - Missing field '{field}' in result"
