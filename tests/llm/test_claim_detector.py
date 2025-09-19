import asyncio
from pathlib import Path

import pytest

from lib.models.agent_test_case import AgentTestCase
from lib.services.file import create_file_document_from_path
from lib.agents.claim_detector import (
    ClaimResponse,
    claim_detector_agent,
)
from tests.datasets.loader import load_dataset


TESTS_DIR = Path(__file__).parent.parent


def _data(path: str) -> str:
    return str(TESTS_DIR / path)


def _build_cases() -> list[AgentTestCase]:
    # Load dataset from YAML
    dataset_path = str(TESTS_DIR / "datasets" / "claim_detector.yaml")
    dataset = load_dataset(dataset_path)

    # Test configuration - hardcoded for this specific test
    strict_fields = {
        "claims": {
            "__all__": {
                "text",
                "needs_substantiation",
            }
        }
    }
    llm_fields = {
        "claims": {
            "__all__": {
                "claim",
            }
        }
    }

    cases: list[AgentTestCase] = []

    for test_case in dataset.items:
        # Load main document from input
        main_path = _data(test_case.input["main_document"])
        main_doc = asyncio.run(create_file_document_from_path(main_path))

        cases.append(
            AgentTestCase(
                name=test_case.name,
                agent=claim_detector_agent,
                response_model=ClaimResponse,
                prompt_kwargs={
                    "full_document": main_doc.markdown,
                    "chunk": test_case.input["chunk"],
                },
                expected_dict=test_case.expected_output,
                strict_fields=strict_fields,
                llm_fields=llm_fields,
            )
        )

    return cases


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _build_cases(), ids=lambda case: case.name)
async def test_claim_detector_agent_cases(case: AgentTestCase):
    await case.run()
    eval_result = await case.compare_results()
    assert eval_result.passed, f"{case.name}: {eval_result.rationale}"
