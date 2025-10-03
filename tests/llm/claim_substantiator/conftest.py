"""Claim substantiator specific test utilities."""

import asyncio
import re
from typing import Optional

from lib.agents.claim_substantiator import (
    ClaimSubstantiationResult,
    claim_substantiator_agent,
)
from lib.agents.formatting_utils import (
    format_audience_context,
    format_cited_references,
    format_domain_context,
    format_supporting_documents_prompt_section,
)
from lib.models.agent_test_case import AgentTestCase
from tests.conftest import TESTS_DIR, build_supporting_documents_block, load_document
from tests.datasets.loader import load_dataset


def extract_paragraph_from_chunk(full_document: str, chunk: str) -> str:
    """
    Extract paragraph context from chunk.

    For test purposes, we detect the paragraph that contains the chunk breaking the full document into paragraphs.

    In production, state.get_paragraph(chunk.paragraph_index) reconstructs
    the full paragraph from all chunks sharing the same paragraph_index.
    """

    paragraphs = full_document.split("\n")
    for paragraph in paragraphs:
        if chunk in paragraph:
            return paragraph

    raise ValueError(f"Chunk not found in full document: {chunk}")


def build_test_cases_from_dataset(
    dataset_name: str,
    strict_fields: Optional[set[str]] = None,
    llm_fields: Optional[set[str]] = None,
) -> list[AgentTestCase]:
    """
    Build test cases from a YAML dataset.

    Args:
        dataset_name: Name of the dataset file (without .yaml extension)
        strict_fields: Fields that must match exactly (overrides YAML config if provided)
        llm_fields: Fields that are evaluated by LLM comparison (overrides YAML config if provided)

    Returns:
        List of AgentTestCase objects ready for parametrized testing
    """
    # Load dataset from YAML
    dataset_path = str(
        TESTS_DIR / "datasets" / "claim_substantiator" / f"{dataset_name}.yaml"
    )
    dataset = load_dataset(dataset_path)

    # Get test configuration from dataset or use provided/default values
    test_config = dataset.test_config
    if strict_fields is None:
        if test_config and test_config.strict_fields:
            strict_fields = test_config.strict_fields

    if llm_fields is None:
        if test_config and test_config.llm_fields:
            llm_fields = test_config.llm_fields

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

        # Extract paragraph from chunk
        # Note: In production, this would be state.get_paragraph(paragraph_index)
        # For tests, we use the chunk itself as a reasonable approximation
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
