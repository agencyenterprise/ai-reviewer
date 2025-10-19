"""RAG-based claim substantiation tests.

This test suite uses RAG (Retrieval Augmented Generation) for claim verification,
which retrieves relevant passages from supporting documents instead of passing
full documents in the prompt. Results can be compared with test_claim_verifier.py
to evaluate the effectiveness of the RAG approach.
"""

import pytest

from lib.agents.claim_extractor import Claim, ClaimResponse
from lib.agents.claim_verifier import ClaimSubstantiationResult
from lib.services.file import FileDocument
from lib.workflows.claim_substantiation.nodes.index_supporting_documents import (
    index_supporting_documents,
)
from lib.workflows.claim_substantiation.nodes.verify_claims import (
    _verify_chunk_claims_rag,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
    SubstantiationWorkflowConfig,
)
from tests.conftest import extract_paragraph_from_chunk
from tests.llm.test_helpers import (
    compare_claim_substantiation_result,
    load_claim_verifier_dataset,
)


async def _run_rag_verification(
    main_doc: FileDocument,
    supporting_docs: list[FileDocument],
    chunk_text: str,
    claim_text: str,
    domain: str | None,
    target_audience: str | None,
) -> ClaimSubstantiationResult:
    """Run RAG-based claim verification for a single claim."""

    config = SubstantiationWorkflowConfig(
        use_rag=True,
        domain=domain,
        target_audience=target_audience,
        session_id=f"test_rag_{id(main_doc)}",
    )

    paragraph = extract_paragraph_from_chunk(main_doc.markdown, chunk_text)

    # Find paragraph index (simplified - assumes chunk is at start of paragraph)
    paragraphs = main_doc.markdown.split("\n\n")
    paragraph_index = 0
    for i, para in enumerate(paragraphs):
        if chunk_text in para:
            paragraph_index = i
            break

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

    state = ClaimSubstantiatorState(
        file=main_doc,
        supporting_files=supporting_docs,
        config=config,
        chunks=[chunk],
    )

    await index_supporting_documents(state)

    verified_chunk = await _verify_chunk_claims_rag(state, chunk)

    if verified_chunk.substantiations:
        return verified_chunk.substantiations[0]
    else:
        raise ValueError("No substantiation results returned")


def _build_cases():
    """Build test cases from dataset using RAG verification."""
    test_cases, strict_fields, llm_fields = load_claim_verifier_dataset()

    return [
        {
            **case,
            "name": f"{case['name']}_rag",
            "strict_fields": strict_fields,
            "llm_fields": llm_fields,
        }
        for case in test_cases
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _build_cases(), ids=lambda case: case["name"])
async def test_claim_verifier_rag(case):
    """Test RAG-based claim substantiation cases.

    These tests use the same dataset and evaluation criteria as test_claim_verifier.py,
    allowing for direct comparison between the full-text and RAG approaches.
    """
    result = await _run_rag_verification(
        main_doc=case["main_doc"],
        supporting_docs=case["supporting_docs"],
        chunk_text=case["chunk"],
        claim_text=case["claim_text"],
        domain=case["domain"],
        target_audience=case["target_audience"],
    )

    compare_claim_substantiation_result(
        expected_output=case["expected_output"],
        actual_result=result,
        strict_fields=case["strict_fields"],
        llm_fields=case["llm_fields"],
        test_name=case["name"],
    )
