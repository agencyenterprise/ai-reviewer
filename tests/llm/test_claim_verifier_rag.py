"""RAG-based claim substantiation tests.

This test suite uses RAG (Retrieval Augmented Generation) for claim verification,
which retrieves relevant passages from supporting documents instead of passing
full documents in the prompt. Results can be compared with test_claim_verifier.py
to evaluate the effectiveness of the RAG approach.
"""

import pytest
from typing import Any, Dict, Optional

from langchain_core.runnables.config import RunnableConfig

from lib.agents.claim_extractor import Claim, ClaimResponse
from lib.agents.claim_verifier import ClaimSubstantiationResult
from lib.models.agent_test_case import AgentTestCase
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
from tests.llm.test_helpers import load_claim_verifier_dataset


class RAGClaimVerifierWrapper:
    """Lightweight wrapper to make RAG verification work with AgentTestCase.

    This wrapper provides an Agent-like interface for the RAG-based claim
    verification workflow, allowing it to be tested using the standard
    AgentTestCase infrastructure.
    """

    name: str = "RAG Claim Verifier"
    description: str = "RAG-based claim verification workflow"

    async def ainvoke(
        self, prompt_kwargs: Dict[str, Any], config: Optional[RunnableConfig] = None
    ) -> ClaimSubstantiationResult:
        """Execute RAG-based claim verification.

        Args:
            prompt_kwargs: Dictionary containing:
                - main_doc: The main document being verified
                - supporting_docs: List of supporting documents
                - chunk_text: The text chunk containing the claim
                - claim_text: The claim to verify
                - domain: Optional domain context
                - target_audience: Optional target audience
            config: Optional configuration (unused but required for Agent interface)

        Returns:
            ClaimSubstantiationResult with verification results
        """
        # Extract parameters
        main_doc = prompt_kwargs["main_doc"]
        supporting_docs = prompt_kwargs["supporting_docs"]
        chunk_text = prompt_kwargs["chunk_text"]
        claim_text = prompt_kwargs["claim_text"]
        domain = prompt_kwargs.get("domain")
        target_audience = prompt_kwargs.get("target_audience")

        # Build config
        workflow_config = SubstantiationWorkflowConfig(
            use_rag=True,
            domain=domain,
            target_audience=target_audience,
            session_id=(
                config.get("metadata", {}).get("langfuse_session_id")
                if config
                else None
            ),
        )

        # Extract paragraph context
        paragraph = extract_paragraph_from_chunk(main_doc.markdown, chunk_text)

        # Find paragraph index
        paragraphs = main_doc.markdown.split("\n\n")
        paragraph_index = 0
        for i, para in enumerate(paragraphs):
            if chunk_text in para:
                paragraph_index = i
                break

        # Create chunk with claim
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
            citations=None,
            claim_common_knowledge_results=[],
        )

        # Create state and run verification
        state = ClaimSubstantiatorState(
            file=main_doc,
            supporting_files=supporting_docs,
            config=workflow_config,
            chunks=[chunk],
        )

        await index_supporting_documents(state)
        verified_chunk = await _verify_chunk_claims_rag(state, chunk)

        if verified_chunk.substantiations:
            return verified_chunk.substantiations[0]
        else:
            raise ValueError("No substantiation results returned")


# Create singleton instance
rag_claim_verifier_agent = RAGClaimVerifierWrapper()


def _build_cases():
    """Build test cases from dataset using RAG verification."""
    test_cases, strict_fields, llm_fields = load_claim_verifier_dataset()

    cases = []
    for case in test_cases:
        # Build prompt kwargs that match the wrapper's expected interface
        prompt_kwargs = {
            "main_doc": case["main_doc"],
            "supporting_docs": case["supporting_docs"],
            "chunk_text": case["chunk"],
            "claim_text": case["claim_text"],
            "domain": case["domain"],
            "target_audience": case["target_audience"],
        }

        cases.append(
            AgentTestCase(
                name=f"{case['name']}_rag",
                agent=rag_claim_verifier_agent,
                response_model=ClaimSubstantiationResult,
                prompt_kwargs=prompt_kwargs,
                expected_dict=case["expected_output"],
                strict_fields=strict_fields,
                llm_fields=llm_fields,
            )
        )

    return cases


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _build_cases(), ids=lambda case: case.name)
async def test_claim_verifier_rag(case: AgentTestCase):
    """Test RAG-based claim substantiation cases.

    These tests use the same dataset and evaluation criteria as test_claim_verifier.py,
    allowing for direct comparison between the full-text and RAG approaches.
    """
    await case.run()
    eval_result = await case.compare_results()

    assert eval_result.passed, f"{case.name}: {eval_result.rationale}"
