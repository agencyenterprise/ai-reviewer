import asyncio
import json
import os
from pathlib import Path

import pytest

from lib.services.file import create_file_document_from_path
from lib.agents.reference_extractor import (
    ReferenceExtractorResponse,
    reference_extractor_agent,
)
from lib.agents.tools import format_supporting_documents_prompt_section_multiple


TESTS_DIR = Path(__file__).parent.parent
TESTS_JSON = TESTS_DIR / "agents" / "reference_extractor_tests.json"


def _data(path: str) -> str:
    return str(TESTS_DIR / path)


def _load_cases() -> list[dict]:
    with open(TESTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cases", [])


async def _build_supporting_documents_block(paths: list[str]) -> str:
    """Mimic the workflow node's supporting docs formatting for consistency."""
    docs = [await create_file_document_from_path(_data(rel_path)) for rel_path in paths]

    return await format_supporting_documents_prompt_section_multiple(
        docs, truncate_at_character_count=1000
    )


def _endswith_or_equal(a: str, b: str) -> bool:
    if not a or not b:
        return False
    a_low, b_low = a.lower(), b.lower()
    return a_low.endswith(b_low) or b_low.endswith(a_low)


@pytest.mark.live
@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c.get("name", "case"))
def test_reference_extractor_live(case: dict):
    main_path = _data(os.path.join(case["data_dir"], case["main_document"]))
    supporting_paths = [
        _data(os.path.join(case["data_dir"], path))
        for path in case.get("supporting_documents", [])
    ]
    expected_result_json: dict = case.get("expected", {})
    expected_result = ReferenceExtractorResponse.model_validate(expected_result_json)

    main_doc = asyncio.run(create_file_document_from_path(main_path))
    supporting_block = asyncio.run(_build_supporting_documents_block(supporting_paths))

    result = asyncio.run(
        reference_extractor_agent.apply(
            {
                "full_document": main_doc.markdown,
                "supporting_documents": supporting_block,
            }
        )
    )

    returned = list(result.references or [])

    # Basic sanity: should extract at least as many as expected
    assert len(returned) >= len(
        expected_result.references
    ), f"Expected at least {len(expected_result.references)} references, got {len(returned)}"

    # For each expected item, find a matching returned item by associated index/name
    for exp in expected_result.references:

        exp_has = exp.has_associated_supporting_document
        exp_idx = exp.index_of_associated_supporting_document
        exp_name = exp.name_of_associated_supporting_document

        matched = None
        for got in returned:
            got_has = got.has_associated_supporting_document
            got_idx = got.index_of_associated_supporting_document
            got_name = got.name_of_associated_supporting_document

            index_match = got_idx == exp_idx
            name_match = _endswith_or_equal(got_name, exp_name)
            has_match = got_has == exp_has

            if has_match and (index_match or name_match):
                matched = got
                break

        assert matched is not None, (
            "No matching extracted reference found for expected entry with "
            f"index={exp_idx}, name='{exp_name}'. Returned: "
            f"[{', '.join(str(getattr(r, 'name_of_associated_supporting_document', '')) for r in returned)}]"
        )
