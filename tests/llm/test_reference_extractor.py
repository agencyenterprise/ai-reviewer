import os
from pathlib import Path

import pytest

from lib.models.agent_test_case import AgentTestCase
from lib.services.file import create_file_document_from_path
from lib.agents.reference_extractor import (
    ReferenceExtractorResponse,
    reference_extractor_agent,
)
from lib.agents.tools import format_supporting_documents_prompt_section_multiple


TESTS_DIR = Path(__file__).parent.parent


def _data(path: str) -> str:
    return str(TESTS_DIR / path)


async def _build_supporting_block(paths: list[str]) -> str:
    docs = [await create_file_document_from_path(_data(p)) for p in paths]
    return await format_supporting_documents_prompt_section_multiple(
        docs, truncate_at_character_count=1000
    )


async def _build_cases() -> list[AgentTestCase]:
    strict_fields = {
        # Validate per-reference fields for all items
        "references": {
            "__all__": {
                # Keep checks robust and deterministic
                "text",
                "has_associated_supporting_document",
                "index_of_associated_supporting_document",
                "name_of_associated_supporting_document",
            },
        }
    }

    cases: list[AgentTestCase] = []

    # Load full document once
    main_path = _data(os.path.join("data", "case_1", "main_document.md"))
    main_doc = await create_file_document_from_path(main_path)

    # case_1-basic
    support_paths_basic = [
        os.path.join("data", "case_1", "supporting_1.md"),
        os.path.join("data", "case_1", "supporting_2.md"),
        os.path.join("data", "case_1", "supporting_3.md"),
    ]
    supporting_block_basic = await _build_supporting_block(support_paths_basic)
    cases.append(
        AgentTestCase(
            name="reference_case_basic",
            agent=reference_extractor_agent,
            response_model=ReferenceExtractorResponse,
            prompt_kwargs={
                "full_document": main_doc.markdown,
                "supporting_documents": supporting_block_basic,
            },
            expected_dict={
                "references": [
                    {
                        "text": "Smith, J. (2020). The Effects of Widgets on Gadgets. Journal of Widgetry.",
                        "has_associated_supporting_document": True,
                        "index_of_associated_supporting_document": 1,
                        "name_of_associated_supporting_document": "supporting_1.md",
                    },
                    {
                        "text": "Doe, A.; Roe, B. (2019). A Comprehensive Study of Gizmos. Proceedings of Gizmo Conf.",
                        "has_associated_supporting_document": True,
                        "index_of_associated_supporting_document": 2,
                        "name_of_associated_supporting_document": "supporting_2.md",
                    },
                    {
                        "text": "Smith, A.; Anderson, T. (2017), A Study of The Effect of Cellphones on Writing Ability. Journal of Big Tech.",
                        "has_associated_supporting_document": True,
                        "index_of_associated_supporting_document": 3,
                        "name_of_associated_supporting_document": "supporting_3.md",
                    },
                ]
            },
            strict_fields=strict_fields,
        )
    )

    # case_1-basic-missing-supporting-document
    support_paths_missing = [
        os.path.join("data", "case_1", "supporting_1.md"),
        os.path.join("data", "case_1", "supporting_3.md"),
    ]
    supporting_block_missing = await _build_supporting_block(support_paths_missing)
    cases.append(
        AgentTestCase(
            name="reference_case_missing_support",
            agent=reference_extractor_agent,
            response_model=ReferenceExtractorResponse,
            prompt_kwargs={
                "full_document": main_doc.markdown,
                "supporting_documents": supporting_block_missing,
            },
            expected_dict={
                "references": [
                    {
                        "text": "Smith, J. (2020). The Effects of Widgets on Gadgets. Journal of Widgetry.",
                        "has_associated_supporting_document": True,
                        "index_of_associated_supporting_document": 1,
                        "name_of_associated_supporting_document": "supporting_1.md",
                    },
                    {
                        "text": "Doe, A.; Roe, B. (2019). A Comprehensive Study of Gizmos. Proceedings of Gizmo Conf.",
                        "has_associated_supporting_document": False,
                        "index_of_associated_supporting_document": -1,
                        "name_of_associated_supporting_document": "",
                    },
                    {
                        "text": "Smith, A.; Anderson, T. (2017), A Study of The Effect of Cellphones on Writing Ability. Journal of Big Tech.",
                        "has_associated_supporting_document": True,
                        "index_of_associated_supporting_document": 2,
                        "name_of_associated_supporting_document": "supporting_3.md",
                    },
                ]
            },
            strict_fields=strict_fields,
        )
    )

    # case_1-basic-no-supporting-documents
    support_paths_none: list[str] = []
    supporting_block_none = await _build_supporting_block(support_paths_none)
    cases.append(
        AgentTestCase(
            name="reference_case_no_support",
            agent=reference_extractor_agent,
            response_model=ReferenceExtractorResponse,
            prompt_kwargs={
                "full_document": main_doc.markdown,
                "supporting_documents": supporting_block_none,
            },
            expected_dict={
                "references": [
                    {
                        "text": "Smith, J. (2020). The Effects of Widgets on Gadgets. Journal of Widgetry.",
                        "has_associated_supporting_document": False,
                        "index_of_associated_supporting_document": -1,
                        "name_of_associated_supporting_document": "",
                    },
                    {
                        "text": "Doe, A.; Roe, B. (2019). A Comprehensive Study of Gizmos. Proceedings of Gizmo Conf.",
                        "has_associated_supporting_document": False,
                        "index_of_associated_supporting_document": -1,
                        "name_of_associated_supporting_document": "",
                    },
                    {
                        "text": "Smith, A.; Anderson, T. (2017), A Study of The Effect of Cellphones on Writing Ability. Journal of Big Tech.",
                        "has_associated_supporting_document": False,
                        "index_of_associated_supporting_document": -1,
                        "name_of_associated_supporting_document": "",
                    },
                ]
            },
            strict_fields=strict_fields,
        )
    )

    return cases


@pytest.mark.live
@pytest.mark.asyncio
async def test_reference_extractor_agent_cases():
    cases = await _build_cases()

    for case in cases:
        await case.run()
        eval_result = await case.compare_results()
        assert eval_result.passed, eval_result.rationale
