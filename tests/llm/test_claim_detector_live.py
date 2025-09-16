import asyncio
import json
import os
from pathlib import Path

import pytest
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model

from lib.services.file import create_file_document_from_path
from lib.agents.claim_detector import (
    ClaimResponse,
    claim_detector_agent,
)


TESTS_DIR = Path(__file__).parent.parent
TESTS_JSON = TESTS_DIR / "agents" / "claim_detector_tests.json"


def _data(path: str) -> str:
    return str(TESTS_DIR / path)


def _load_cases() -> list[dict]:
    with open(TESTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cases", [])


class EvalResult(BaseModel):
    match: bool = Field(description="Whether the expected and received results match")
    rationale: str = Field(description="Brief reason for the decision")


def _llm_compare_expected_received(
    expected_json: dict, received_json: dict
) -> EvalResult:
    """Use an LLM to evaluate semantic match of expected vs received claims.

    Ignore order and wording; compare number of claims and whether each expected
    claim is represented by a semantically equivalent 'claim' field in the
    received result. Minor phrasing differences should be considered equivalent.
    """
    grader = init_chat_model("gpt-5", model_provider="openai", temperature=0)
    grader = grader.with_structured_output(EvalResult)

    prompt = ChatPromptTemplate.from_template(
        """
You are a strict evaluator for claim extraction results.

Instructions:
- Compare the EXPECTED and RECEIVED JSON objects for claims extracted from a text chunk.
- Focus ONLY on:
  1) the number of claims, and
  2) the semantic content of each claim (the 'claim' field),
     ignoring minor wording differences and ignoring order.
- Do NOT consider rationale or 'text' fields.
- If an expected claim is present with the same meaning in the received set, count it as a match.
- If counts differ or any expected claim is missing (semantically), return match=false.

Return a boolean 'match' and a short 'reason'.

EXPECTED JSON:
```
{expected}
```

RECEIVED JSON:
```
{received}
```
"""
    )

    messages = prompt.format_messages(
        expected=json.dumps(expected_json, ensure_ascii=False, indent=2),
        received=json.dumps(received_json, ensure_ascii=False, indent=2),
    )

    result: EvalResult = grader.invoke(messages)
    return result


@pytest.mark.live
@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c.get("name", "case"))
def test_detect_claims_live(case: dict):
    main_path = _data(os.path.join(case["data_dir"], case["main_document"]))
    chunk = case.get("chunk", "")
    expected_result_json: dict = case.get("expected", {})

    # Validate expected JSON against schema
    ClaimResponse.model_validate(expected_result_json)

    main_doc = asyncio.run(create_file_document_from_path(main_path))

    received: ClaimResponse = asyncio.run(
        claim_detector_agent.apply(
            {
                "full_document": main_doc.markdown,
                "chunk": chunk,
            }
        )
    )

    received_json = json.loads(ClaimResponse.model_validate(received).model_dump_json())

    eval_result = _llm_compare_expected_received(
        expected_json=expected_result_json, received_json=received_json
    )

    assert eval_result.match, f"""LLM grader mismatch: {eval_result.rationale}.
Expected: {expected_result_json}
Received: {received_json}"""
