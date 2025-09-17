import os
from pathlib import Path
from typing import List

import pytest

from lib.models.AgentTestCase import AgentTestCase
from lib.services.file import create_file_document_from_path
from lib.agents.citation_detector import (
    CitationResponse,
    citation_detector_agent,
)


TESTS_DIR = Path(__file__).parent.parent
DATA_DIR = TESTS_DIR / "data" / "case_1"


def _data(path: str) -> str:
    return str(TESTS_DIR / path)


def _build_cases() -> List[AgentTestCase]:
    bibliography = (
        "1. Smith, J. (2020). The Effects of Widgets on Gadgets. Journal of Widgetry.\n\n"
        "2. Doe, A.; Roe, B. (2019). A Comprehensive Study of Gizmos. Proceedings of Gizmo Conf.\n\n"
        "3. Smith, A.; Anderson, T. (2017), A Study of The Effect of Cellphones on Writing Ability. Journal of Big Tech."
    )
    strict_fields = {
        "citations": {
            "__all__": {
                "text",
                "needs_bibliography",
                "associated_bibliography",
                "index_of_associated_bibliography",
            },
        }
    }

    cases: list[AgentTestCase] = []

    # case_1-example-1
    cases.append(
        AgentTestCase(
            name="citation_case_1",
            agent=citation_detector_agent,
            response_model=CitationResponse,
            prompt_kwargs={
                # full_document injected later after file load
                "full_document": "",
                "bibliography": bibliography,
                "chunk": "Prior work such as Smith (2020) and Doe and Roe (2019) provide useful background/insights.",
            },
            expected_json={
                "citations": [
                    {
                        "text": "Smith (2020)",
                        "type": "bibliography",
                        "format": "author (year)",
                        "needs_bibliography": True,
                        "associated_bibliography": "Smith, J. (2020). The Effects of Widgets on Gadgets. Journal of Widgetry.",
                        "index_of_associated_bibliography": 1,
                        "rationale": "",
                    },
                    {
                        "text": "Doe and Roe (2019)",
                        "type": "bibliography",
                        "format": "author (year)",
                        "needs_bibliography": True,
                        "associated_bibliography": "Doe, A.; Roe, B. (2019). A Comprehensive Study of Gizmos. Proceedings of Gizmo Conf.",
                        "index_of_associated_bibliography": 2,
                        "rationale": "",
                    },
                ],
                "rationale": "",
            },
            strict_fields=strict_fields,
            # We'll do custom strict checks; AgentTestCase compare_ methods not used here
        )
    )

    # case_1-example-2
    cases.append(
        AgentTestCase(
            name="citation_case_2",
            agent=citation_detector_agent,
            response_model=CitationResponse,
            prompt_kwargs={
                "full_document": "",
                "bibliography": bibliography,
                "chunk": "In this article, we will review what some of the other works in the field, including (Smith, 2017) have found in this domain.",
            },
            expected_json={
                "citations": [
                    {
                        "text": "(Smith, 2017)",
                        "type": "bibliography",
                        "format": "(author, year)",
                        "needs_bibliography": True,
                        "associated_bibliography": "Smith, A.; Anderson, T. (2017), A Study of The Effect of Cellphones on Writing Ability. Journal of Big Tech.",
                        "index_of_associated_bibliography": 3,
                        "rationale": "",
                    }
                ],
                "rationale": "",
            },
            strict_fields=strict_fields,
        )
    )

    # case_1-example-3 (no citations)
    cases.append(
        AgentTestCase(
            name="citation_case_3",
            agent=citation_detector_agent,
            response_model=CitationResponse,
            prompt_kwargs={
                "full_document": "",
                "bibliography": bibliography,
                "chunk": "We conducted experiments using standard gizmo benchmarks.",
            },
            expected_json={
                "citations": [],
                "rationale": "",
            },
            strict_fields=strict_fields,
        ),
    )

    return cases


@pytest.mark.live
@pytest.mark.asyncio
async def test_citation_detector_agent_cases():
    cases = _build_cases()

    # Load full document once
    main_path = _data(os.path.join("data", "case_1", "main_document.md"))
    main_doc = await create_file_document_from_path(main_path)

    failures: list[str] = []
    for case in cases:
        # inject full document into prompt
        case.prompt_kwargs["full_document"] = main_doc.markdown

        await case.run()
        eval_result = await case.compare_results()
        if not eval_result.passed:
            failures.append(f"{case.name}: {eval_result.rationale}")

    if failures:
        pytest.fail("\n" + "\n".join(failures))
