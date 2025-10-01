"""Basic claim substantiation tests."""

import pytest

from tests.llm.claim_substantiator.conftest import build_test_cases_from_dataset


def _build_cases():
    """Build test cases from basic dataset."""
    return build_test_cases_from_dataset(
        dataset_name="basic",
        strict_fields={"is_substantiated", "severity"},
        llm_fields={"rationale", "feedback"},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _build_cases(), ids=lambda case: case.name)
async def test_claim_substantiator_basic_cases(case):
    """Test basic claim substantiation cases."""
    await case.run()
    eval_result = await case.compare_results()

    assert eval_result.passed, f"{case.name}: {eval_result.rationale}"
