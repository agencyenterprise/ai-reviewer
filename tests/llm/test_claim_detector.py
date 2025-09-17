import os
from pathlib import Path

import pytest

from lib.models.agent_test_case import AgentTestCase
from lib.services.file import create_file_document_from_path
from lib.agents.claim_detector import (
    ClaimResponse,
    claim_detector_agent,
)


TESTS_DIR = Path(__file__).parent.parent


def _data(path: str) -> str:
    return str(TESTS_DIR / path)


async def _build_cases() -> list[AgentTestCase]:
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

    # Load full document once
    main_path = _data(os.path.join("data", "case_1", "main_document.md"))
    main_doc = await create_file_document_from_path(main_path)

    cases: list[AgentTestCase] = []

    # case_1-claims-example-1
    cases.append(
        AgentTestCase(
            name="claim_case_1",
            agent=claim_detector_agent,
            response_model=ClaimResponse,
            prompt_kwargs={
                "full_document": main_doc.markdown,
                "chunk": "Prior work such as Smith (2020) and Doe and Roe (2019) provide useful background/insights.",
            },
            expected_dict={
                "claims": [
                    {
                        "text": "Prior work such as Smith (2020) and Doe and Roe (2019) provide useful background/insights.",
                        "claim": "Smith (2020) provides useful background/insights.",
                        "needs_substantiation": True,
                        "rationale": "",
                    },
                    {
                        "text": "Prior work such as Smith (2020) and Doe and Roe (2019) provide useful background/insights.",
                        "claim": "Doe and Roe (2019) provides useful background/insights.",
                        "needs_substantiation": True,
                        "rationale": "",
                    },
                ],
                "rationale": "",
            },
            strict_fields=strict_fields,
            llm_fields=llm_fields,
        )
    )

    # case_1-claims-example-2
    cases.append(
        AgentTestCase(
            name="claim_case_2",
            agent=claim_detector_agent,
            response_model=ClaimResponse,
            prompt_kwargs={
                "full_document": main_doc.markdown,
                "chunk": "Of note, cellphones have a positive impact on the user's writing proficiency in most countries (Smith, 2017), making them one of the best widgets out there.",
            },
            expected_dict={
                "claims": [
                    {
                        "text": "cellphones have a positive impact on the user's writing proficiency in most countries (Smith, 2017)",
                        "claim": "Cellphones positively affect users' writing proficiency in most countries.",
                        "needs_substantiation": True,
                        "rationale": "",
                    },
                    {
                        "text": "making them one of the best widgets out there.",
                        "claim": "Cellphones are one of the best widgets.",
                        "needs_substantiation": True,
                        "rationale": "",
                    },
                ],
                "rationale": "",
            },
            strict_fields=strict_fields,
            llm_fields=llm_fields,
        )
    )

    # case_1-claims-example-3-no-claims
    cases.append(
        AgentTestCase(
            name="claim_case_3_no_claims",
            agent=claim_detector_agent,
            response_model=ClaimResponse,
            prompt_kwargs={
                "full_document": main_doc.markdown,
                "chunk": "# Effects of Widgets on System Performance",
            },
            expected_dict={
                "claims": [],
                "rationale": "",
            },
            strict_fields=strict_fields,
            llm_fields=llm_fields,
        )
    )

    return cases


@pytest.mark.live
@pytest.mark.asyncio
async def test_claim_detector_agent_cases():
    cases = await _build_cases()

    failures: list[str] = []
    for case in cases:
        await case.run()
        eval_result = await case.compare_results()
        if not eval_result.passed:
            failures.append(f"{case.name}: {eval_result.rationale}")

    if failures:
        pytest.fail("\n" + "\n".join(failures))
