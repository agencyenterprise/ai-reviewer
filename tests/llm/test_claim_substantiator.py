import asyncio
from pathlib import Path

import pytest

from lib.models.agent_test_case import AgentTestCase
from lib.services.file import create_file_document_from_path
from lib.agents.claim_substantiator import (
    ClaimSubstantiationResult,
    claim_substantiator_agent,
)
from tests.datasets.loader import load_dataset


TESTS_DIR = Path(__file__).parent.parent


def _data(path: str) -> str:
    return str(TESTS_DIR / path)


async def _build_supporting_documents_block(paths: list[str]) -> str:
    """Build supporting documents block from file paths."""
    docs = []
    for path in paths:
        doc = await create_file_document_from_path(_data(path))
        docs.append(doc.markdown)

    return "\n\n---\n\n".join(docs)


def _extract_paragraph_from_claim(full_document: str, claim_text: str) -> str:
    """
    Extract the paragraph containing the claim from the full document.

    Args:
        full_document: The complete document text
        claim_text: The specific claim text to find within the document

    Returns:
        The paragraph containing the claim, or the full document if not found
    """
    # Split document into paragraphs (by double newlines)
    paragraphs = full_document.split("\n\n")

    # Find the paragraph that contains the claim
    for paragraph in paragraphs:
        if claim_text.strip() in paragraph:
            return paragraph.strip()

    # If no paragraph contains the claim, raise an error
    raise ValueError(
        f"No paragraph containing the claim found in the full document: '{claim_text}'"
    )


def _build_cases() -> list[AgentTestCase]:
    # Load dataset from YAML
    dataset_path = str(TESTS_DIR / "datasets" / "claim_substantiator.yaml")
    dataset = load_dataset(dataset_path)

    # Test configuration - hardcoded for this specific test
    strict_fields = {
        "is_substantiated",
        # "severity",
    }
    llm_fields = {
        "rationale",
        "feedback",
    }

    cases: list[AgentTestCase] = []

    for test_case in dataset.items:
        # Load main document from input
        main_path = _data(test_case.input["main_document"])
        main_doc = asyncio.run(create_file_document_from_path(main_path))

        # Build supporting documents block from input
        supporting_documents_block = asyncio.run(
            _build_supporting_documents_block(test_case.input["supporting_documents"])
        )

        claim_text = test_case.input["claim"]
        chunk_text = test_case.input["chunk"]

        # Extract the paragraph containing the claim
        paragraph = _extract_paragraph_from_claim(main_doc.markdown, chunk_text)

        cases.append(
            AgentTestCase(
                name=test_case.name,
                agent=claim_substantiator_agent,
                response_model=ClaimSubstantiationResult,
                prompt_kwargs={
                    "full_document": main_doc.markdown,
                    "paragraph": paragraph,
                    "chunk": chunk_text,
                    "claim": claim_text,
                    "cited_references": supporting_documents_block,
                    "domain_context": "",
                    "audience_context": "",
                },
                expected_dict=test_case.expected_output,
                strict_fields=strict_fields,
                llm_fields=llm_fields,
            )
        )

    return cases


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _build_cases(), ids=lambda case: case.name)
async def test_claim_substantiator_agent_cases(case: AgentTestCase):
    await case.run()
    eval_result = await case.compare_results()
    assert eval_result.passed, f"{case.name}: {eval_result.rationale}"
