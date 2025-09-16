import asyncio
import json
import os
from pathlib import Path

import pytest

from lib.agents.citation_detector import CitationResponse
from lib.services.file import create_file_document_from_path
from lib.agents.citation_detector import (
    CitationResponse,
    citation_detector_agent,
)


TESTS_DIR = Path(__file__).parent.parent
TESTS_JSON = TESTS_DIR / "agents" / "citation_detector_tests.json"


def _data(path: str) -> str:
    return str(TESTS_DIR / path)


def _load_cases() -> list[dict]:
    with open(TESTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cases", [])


def _endswith_or_equal(a: str, b: str) -> bool:
    if not a or not b:
        return False
    a_low, b_low = a.lower(), b.lower()
    return a_low.endswith(b_low) or b_low.endswith(a_low)


@pytest.mark.live
@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c.get("name", "case"))
def test_reference_extractor_live(case: dict):
    main_path = _data(os.path.join(case["data_dir"], case["main_document"]))
    bibliography = case.get("bibliography", "")
    chunk = case.get("chunk", "")
    expected_result_json: dict = case.get("expected", {})
    expected_result = CitationResponse.model_validate(expected_result_json)

    main_doc = asyncio.run(create_file_document_from_path(main_path))

    result = asyncio.run(
        citation_detector_agent.apply(
            {
                "full_document": main_doc.markdown,
                "bibliography": bibliography,
                "chunk": chunk,
            }
        )
    )

    returned = list(result.citations or [])

    # Basic sanity: should extract at least as many as expected
    assert len(returned) >= len(
        expected_result.citations
    ), f"Expected at least {len(expected_result.citations)} citations, got {len(returned)}"

    # For each expected item, find a matching returned item by associated index/name
    for exp in expected_result.citations:

        exp_text = exp.text
        exp_needs_bibliography = exp.needs_bibliography
        exp_associated_bibliography = exp.associated_bibliography
        exp_idx = exp.index_of_associated_bibliography

        matched = None
        for got in returned:
            got_text = got.text
            got_needs_bibliography = got.needs_bibliography
            got_associated_bibliography = got.associated_bibliography
            got_idx = got.index_of_associated_bibliography

            text_match = got_text == exp_text
            needs_bibliography_match = got_needs_bibliography == exp_needs_bibliography
            associated_bibliography_match = (
                got_associated_bibliography == exp_associated_bibliography
            )
            index_match = got_idx == exp_idx

            if (
                text_match
                and needs_bibliography_match
                and associated_bibliography_match
                and index_match
            ):
                matched = got
                break

        assert matched is not None, (
            "No matching extracted reference found for expected entry with "
            f"index={exp_idx}, text='{exp_text}'. Returned: "
            f"[{', '.join(str(getattr(r, 'name_of_associated_supporting_document', '')) for r in returned)}]"
        )
