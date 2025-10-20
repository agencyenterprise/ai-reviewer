"""Shared test helpers for claim verifier tests."""

import asyncio
from typing import Any, Dict, List, Set

from tests.conftest import TESTS_DIR, load_document
from tests.datasets.loader import load_dataset


def load_claim_verifier_dataset() -> tuple[List[Dict[str, Any]], Set[str], Set[str]]:
    """Load claim verifier dataset and return test cases with configuration.

    Returns:
        Tuple of (test_cases, strict_fields, llm_fields)
    """
    dataset_path = str(TESTS_DIR / "datasets" / "claim_verifier.yaml")
    dataset = load_dataset(dataset_path)

    test_config = dataset.test_config
    strict_fields = set()
    llm_fields = set()
    if test_config:
        strict_fields = test_config.strict_fields or set()
        llm_fields = test_config.llm_fields or set()

    test_cases = []
    for test_case in dataset.items:
        main_doc = asyncio.run(load_document(test_case.input["main_document"]))
        supporting_docs = [
            asyncio.run(load_document(doc))
            for doc in test_case.input.get("supporting_documents", [])
        ]

        test_cases.append(
            {
                "name": test_case.name,
                "main_doc": main_doc,
                "supporting_docs": supporting_docs,
                "chunk": test_case.input["chunk"],
                "claim_text": test_case.input["claim"],
                "domain": test_case.input.get("domain"),
                "target_audience": test_case.input.get("target_audience"),
                "expected_output": test_case.expected_output,
            }
        )

    return test_cases, strict_fields, llm_fields
