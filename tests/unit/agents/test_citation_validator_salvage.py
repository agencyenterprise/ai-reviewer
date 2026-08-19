"""Tests for salvaging assessments from a truncated citation-validator response.

Reproduces the failure seen in production: OpenAI ends the response with
`status: "incomplete"`, LangChain's `json.loads` raises over the partial text,
and everything the model had already written is discarded. The agent now keeps
the complete assessments and reports the section as partial.

These drive `ainvoke` with the LLM call stubbed out, so the exception handling
under test is the one that actually runs, not a copy of it.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain.agents.structured_output import StructuredOutputValidationError
from langchain_core.messages import AIMessage

from lib.agents import citation_validator
from lib.agents.citation_validator import (
    CitationAssessment,
    CitationValidatorAgent,
    PartialSectionValidationError,
    SectionValidationResult,
)
from lib.agents.claim_verifier import EvidenceAlignmentLevel
from lib.services.file_artifacts_service.file_artifacts_service_type import (
    FileArtifactsServiceType,
)
from lib.workflows.context import ContextSchema
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

_PROMPT_KWARGS = {
    "main_file_id": "file-123",
    "start_line": 89,
    "end_line": 99,
    "section_headings": "Introduction",
    "reference_file_map": "[1] The Economist 2024 -> file-abc",
    "domain_context": "",
    "audience_context": "",
    "headings": ["Introduction"],
}


def _parse_failure(payload: str) -> StructuredOutputValidationError:
    """The exception LangChain raises when the model's JSON is cut off."""
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


def _agent() -> CitationValidatorAgent:
    context = ContextSchema(
        project_id="project-1",
        workflow_run_id="run-1",
        file_artifacts_service=MagicMock(spec=FileArtifactsServiceType),
    )
    agent = CitationValidatorAgent(context)
    # Pre-seed the cached model so no API key or network is needed.
    agent._llm = MagicMock()
    return agent


async def _invoke_failing_with(error: Exception):
    """Run `ainvoke` against a graph whose model call raises `error`."""
    graph = SimpleNamespace(ainvoke=AsyncMock(side_effect=error))
    with patch.object(citation_validator, "create_agent", return_value=graph):
        return await _agent().ainvoke(_PROMPT_KWARGS)


@pytest.mark.asyncio
async def test_returns_the_structured_result_when_the_response_is_complete():
    """The salvage path must stay out of the way of a healthy response."""
    expected = SectionValidationResult(
        issues=[
            CitationAssessment(
                quoted_text="A well-supported claim (Smith, 2020).",
                line_start=12,
                line_end=12,
                evidence_alignment=EvidenceAlignmentLevel.SUPPORTED,
                rationale="The source states exactly this.",
                feedback="No changes needed",
            )
        ]
    )
    messages = [AIMessage(content="done")]
    graph = SimpleNamespace(
        ainvoke=AsyncMock(return_value={"structured_response": expected, "messages": messages})
    )

    with patch.object(citation_validator, "create_agent", return_value=graph):
        result, returned_messages = await _agent().ainvoke(_PROMPT_KWARGS)

    assert result is expected
    assert returned_messages is messages


@pytest.mark.asyncio
async def test_salvages_the_assessments_written_before_the_cut():
    with pytest.raises(PartialSectionValidationError) as raised:
        await _invoke_failing_with(_parse_failure(TRUNCATED_PAYLOAD))

    issues = raised.value.result.issues
    assert len(issues) == 2
    assert issues[0].evidence_alignment == "supported"
    assert issues[1].evidence_alignment == "partially_supported"
    # Nested evidence survives intact, not just the scalar fields.
    assert issues[0].evidence_sources[0].file_id == "57ebc998-2286-4cc1-bbba-ec094039b27a"


@pytest.mark.asyncio
async def test_partial_error_message_reports_what_was_recovered():
    with pytest.raises(PartialSectionValidationError) as raised:
        await _invoke_failing_with(_parse_failure(TRUNCATED_PAYLOAD))

    assert "recovered 2 complete citation assessment(s)" in str(raised.value)


@pytest.mark.asyncio
async def test_partial_error_keeps_the_underlying_failure_reachable():
    """The message stays short for the UI; the cause carries the detail."""
    original = _parse_failure(TRUNCATED_PAYLOAD)

    with pytest.raises(PartialSectionValidationError) as raised:
        await _invoke_failing_with(original)

    assert raised.value.source is original
    assert raised.value.__cause__ is original
    assert "Unterminated string" in str(raised.value.source)


@pytest.mark.asyncio
async def test_partial_error_keeps_the_response_message_for_debugging():
    with pytest.raises(PartialSectionValidationError) as raised:
        await _invoke_failing_with(_parse_failure(TRUNCATED_PAYLOAD))

    assert [type(m) for m in raised.value.messages] == [AIMessage]


@pytest.mark.asyncio
async def test_provider_diagnostics_stay_reachable_through_the_partial_error():
    """The salvage must not sever the chain the error capture walks."""
    with pytest.raises(PartialSectionValidationError) as raised:
        await _invoke_failing_with(_parse_failure(TRUNCATED_PAYLOAD))

    details = capture_error_details(raised.value)

    assert details.error_type == "PartialSectionValidationError"
    assert details.llm_metadata is not None
    assert details.llm_metadata["incomplete_details"] == {"reason": "content_filter"}
    assert details.raw_model_output == TRUNCATED_PAYLOAD


@pytest.mark.asyncio
async def test_reraises_unchanged_when_nothing_can_be_salvaged():
    """Cut before the first assessment completed — no partial result to offer."""
    original = _parse_failure('{"issues":[{"quoted_text":"cut immediately')

    with pytest.raises(StructuredOutputValidationError) as raised:
        await _invoke_failing_with(original)

    assert raised.value is original


@pytest.mark.asyncio
async def test_unsalvageable_reraise_keeps_the_original_failure_site():
    """A bare re-raise must not point the traceback at the handler."""

    def failing_model_call(*_args, **_kwargs):
        raise _parse_failure('{"issues":[{"quoted_text":"cut immediately')

    graph = SimpleNamespace(ainvoke=AsyncMock(side_effect=failing_model_call))
    with patch.object(citation_validator, "create_agent", return_value=graph):
        with pytest.raises(StructuredOutputValidationError) as raised:
            await _agent().ainvoke(_PROMPT_KWARGS)

    traceback_text = capture_error_details(raised.value).traceback or ""
    assert "failing_model_call" in traceback_text
    assert "Unterminated string" in traceback_text


@pytest.mark.asyncio
async def test_reraises_unchanged_when_the_error_carries_no_response():
    class _Bare(StructuredOutputValidationError):
        def __init__(self) -> None:
            Exception.__init__(self, "no ai_message here")
            self.ai_message = None  # type: ignore[assignment]

    original = _Bare()

    with pytest.raises(StructuredOutputValidationError) as raised:
        await _invoke_failing_with(original)

    assert raised.value is original


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", ["", "not json at all", "{}"])
async def test_reraises_unchanged_for_unparseable_responses(payload: str):
    ai_message = AIMessage(content=payload)
    original = StructuredOutputValidationError(
        "SectionValidationResult", ValueError("boom"), ai_message
    )

    with pytest.raises(StructuredOutputValidationError) as raised:
        await _invoke_failing_with(original)

    assert raised.value is original
