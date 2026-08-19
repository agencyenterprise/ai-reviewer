"""Tests for salvaging assessments from a truncated citation-validator response.

Reproduces the failure seen in production: OpenAI ends the response with
`status: "incomplete"`, LangChain's `json.loads` raises over the partial text,
and everything the model had already written is discarded. The agent now keeps
the complete assessments and reports the section as partial.
"""

from __future__ import annotations

import json

import pytest
from langchain.agents.structured_output import StructuredOutputValidationError
from langchain_core.messages import AIMessage

from lib.agents.citation_validator import (
    CitationValidatorAgent,
    PartialSectionValidationError,
)
from lib.workflows.error_details import capture_error_details

# Two complete assessments, then a third cut mid-quote — the shape of the
# response that failed on section 8 of the CERN-for-AI document.
TRUNCATED_PAYLOAD = (
    '{"issues":['
    '{"quoted_text":"AI development is decentralized (The Economist, 2024).",'
    '"line_start":91,"line_end":91,"evidence_alignment":"supported",'
    '"rationale":"The cited article describes competition among nations.",'
    '"feedback":"No changes needed",'
    '"evidence_sources":[{"quote":"vying to become AI national champions",'
    '"location":"Article body","file_id":"57ebc998-2286-4cc1-bbba-ec094039b27a"}],'
    '"citation_to_file_mapping":"The Economist (2024) - economist.md"},'
    '{"quoted_text":"One frequent analogy is between AI and nuclear technology.",'
    '"line_start":95,"line_end":95,"evidence_alignment":"partially_supported",'
    '"rationale":"The source covers CERN but not existential risk.",'
    '"feedback":"Add a source discussing the analogy directly.",'
    '"evidence_sources":[]},'
    '{"quoted_text":"A third claim whose quote never finished, in particular at CERN'
)


def _structured_output_error(payload: str) -> StructuredOutputValidationError:
    ai_message = AIMessage(
        content=payload,
        response_metadata={
            "model_name": "gpt-5.5",
            "status": "incomplete",
            "incomplete_details": {"reason": "content_filter"},
        },
    )
    try:
        json.loads(payload)
    except json.JSONDecodeError as decode_error:
        try:
            raise ValueError(
                "Native structured output expected valid JSON for "
                f"SectionValidationResult, but parsing failed: {decode_error}."
            ) from decode_error
        except ValueError as source:
            return StructuredOutputValidationError(
                "SectionValidationResult", source, ai_message
            )
    raise AssertionError("payload was expected to be invalid JSON")


def test_salvages_the_assessments_written_before_the_cut():
    raised = CitationValidatorAgent._salvage_or_reraise(
        _structured_output_error(TRUNCATED_PAYLOAD)
    )

    assert isinstance(raised, PartialSectionValidationError)
    assert len(raised.result.issues) == 2
    assert raised.result.issues[0].evidence_alignment == "supported"
    assert raised.result.issues[1].evidence_alignment == "partially_supported"
    # Nested evidence survives intact, not just the scalar fields.
    assert (
        raised.result.issues[0].evidence_sources[0].file_id
        == "57ebc998-2286-4cc1-bbba-ec094039b27a"
    )


def test_partial_error_message_reports_what_was_recovered():
    raised = CitationValidatorAgent._salvage_or_reraise(
        _structured_output_error(TRUNCATED_PAYLOAD)
    )

    assert "recovered 2 complete citation assessment(s)" in str(raised)
    assert "Unterminated string" in str(raised)


def test_partial_error_keeps_the_response_message_for_debugging():
    raised = CitationValidatorAgent._salvage_or_reraise(
        _structured_output_error(TRUNCATED_PAYLOAD)
    )

    assert isinstance(raised, PartialSectionValidationError)
    assert [type(m) for m in raised.messages] == [AIMessage]


def test_provider_diagnostics_stay_reachable_through_the_partial_error():
    """The salvage must not sever the chain the error capture walks."""
    raised = CitationValidatorAgent._salvage_or_reraise(
        _structured_output_error(TRUNCATED_PAYLOAD)
    )

    details = capture_error_details(raised)

    assert details.error_type == "PartialSectionValidationError"
    assert details.llm_metadata is not None
    assert details.llm_metadata["incomplete_details"] == {"reason": "content_filter"}
    assert details.raw_model_output == TRUNCATED_PAYLOAD


def test_reraises_unchanged_when_nothing_can_be_salvaged():
    """Cut before the first assessment completed — no partial result to offer."""
    error = _structured_output_error('{"issues":[{"quoted_text":"cut immediately')

    raised = CitationValidatorAgent._salvage_or_reraise(error)

    assert raised is error


def test_reraises_unchanged_when_the_error_carries_no_response():
    class _Bare(StructuredOutputValidationError):
        def __init__(self) -> None:
            Exception.__init__(self, "no ai_message here")
            self.ai_message = None  # type: ignore[assignment]

    error = _Bare()

    assert CitationValidatorAgent._salvage_or_reraise(error) is error


@pytest.mark.parametrize("payload", ["", "not json at all", "{}"])
def test_reraises_unchanged_for_unparseable_responses(payload: str):
    ai_message = AIMessage(content=payload)
    error = StructuredOutputValidationError(
        "SectionValidationResult", ValueError("boom"), ai_message
    )

    assert CitationValidatorAgent._salvage_or_reraise(error) is error
