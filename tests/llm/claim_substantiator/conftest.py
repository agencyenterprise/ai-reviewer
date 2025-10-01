"""Claim substantiator specific test utilities."""

import asyncio
from typing import Optional

from lib.models.agent_test_case import AgentTestCase
from lib.agents.claim_substantiator import (
    ClaimSubstantiationResult,
    claim_substantiator_agent,
)
from lib.agents.formatting_utils import format_domain_context, format_audience_context
from tests.datasets.loader import load_dataset
from tests.conftest import (
    TESTS_DIR,
    data_path,
    load_document,
    build_supporting_documents_block,
)


def extract_paragraph_from_chunk(chunk: str) -> str:
    """
    Extract paragraph context from chunk.

    For test purposes, we use the chunk itself as the paragraph since
    we don't have the full paragraph structure from the LLM chunker.

    In production, state.get_paragraph(chunk.paragraph_index) reconstructs
    the full paragraph from all chunks sharing the same paragraph_index.
    """
    return chunk


def build_test_cases_from_dataset(
    dataset_name: str,
    strict_fields: Optional[set[str]] = None,
    llm_fields: Optional[set[str]] = None,
) -> list[AgentTestCase]:
    """
    Build test cases from a YAML dataset.

    Args:
        dataset_name: Name of the dataset file (without .yaml extension)
        strict_fields: Fields that must match exactly
        llm_fields: Fields that are evaluated by LLM comparison

    Returns:
        List of AgentTestCase objects ready for parametrized testing
    """
    # Default field configurations
    if strict_fields is None:
        strict_fields = {"is_substantiated", "severity"}

    if llm_fields is None:
        llm_fields = {"rationale", "feedback"}

    # Load dataset from YAML
    dataset_path = str(
        TESTS_DIR / "datasets" / "claim_substantiator" / f"{dataset_name}.yaml"
    )
    dataset = load_dataset(dataset_path)

    cases: list[AgentTestCase] = []

    for test_case in dataset.items:
        # Load main document
        main_doc = asyncio.run(load_document(test_case.input["main_document"]))

        # Build supporting documents block if provided
        supporting_docs = test_case.input.get("supporting_documents", [])
        supporting_documents_block = asyncio.run(
            build_supporting_documents_block(supporting_docs)
        )

        # Extract inputs
        chunk = test_case.input["chunk"]
        claim_text = test_case.input["claim"]
        domain = test_case.input.get("domain")
        target_audience = test_case.input.get("target_audience")

        # Extract paragraph from chunk
        # Note: In production, this would be state.get_paragraph(paragraph_index)
        # For tests, we use the chunk itself as a reasonable approximation
        paragraph = extract_paragraph_from_chunk(chunk)

        # Build prompt kwargs
        prompt_kwargs = {
            "full_document": main_doc.markdown,
            "paragraph": paragraph,
            "chunk": chunk,
            "claim": claim_text,
            "cited_references": supporting_documents_block,
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
