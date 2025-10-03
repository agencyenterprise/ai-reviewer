"""Common knowledge detection and severity tests."""

import pytest

from tests.llm.claim_substantiator.conftest import build_test_cases_from_dataset


def _build_cases():
    """Build test cases from common knowledge dataset."""
    return build_test_cases_from_dataset(dataset_name="common_knowledge")


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _build_cases(), ids=lambda case: case.name)
async def test_claim_substantiator_common_knowledge_cases(case):
    """
    Test common knowledge detection and severity assignment.

    These tests validate:
    1. Correct identification of common knowledge claims
    2. Appropriate severity levels for common knowledge with quantifiers
    3. Domain and audience context sensitivity
    """
    await case.run()
    eval_result = await case.compare_results()

    assert eval_result.passed, f"{case.name}: {eval_result.rationale}"
