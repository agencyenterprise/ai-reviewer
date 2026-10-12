"""Tests for direct, schema-constrained per-chunk abbreviation extraction."""

import json
from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from lib.agents.abbreviation_chunk_extractor import (
    CHUNK_GUIDANCE,
    AbbreviationChunkExtractorAgent,
    PartialChunkExtractionError,
    build_messages,
)
from lib.services.file_artifacts_service.mock import MockFileArtifactsService
from lib.skills import load_skill_prompt
from lib.workflows.abbreviation_scan_v2.chunk_models import (
    ChunkExtractionResult,
    ChunkOccurrence,
)
from lib.workflows.context import ContextSchema

MARKDOWN = "\n".join(f"line {n}" for n in range(1, 401))
KWARGS: dict[str, Any] = {"markdown": MARKDOWN, "start_line": 10, "end_line": 42}


class StubStructuredModel:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.schema: object = None
        self.kwargs: dict[str, Any] = {}
        self.messages: list[object] = []
        self.config: object = None

    def with_structured_output(self, schema, **kwargs):
        self.schema = schema
        self.kwargs = kwargs
        return self

    async def ainvoke(self, messages, config=None):
        self.messages = messages
        self.config = config
        return self.response


def _agent(
    response: dict[str, Any],
) -> tuple[AbbreviationChunkExtractorAgent, StubStructuredModel]:
    context = ContextSchema(
        project_id="p", file_artifacts_service=MockFileArtifactsService()
    )
    agent = AbbreviationChunkExtractorAgent(context)
    model = StubStructuredModel(response)
    agent._llm = model  # type: ignore[assignment]
    return agent, model


def test_prompt_contains_only_the_numbered_chunk_as_direct_input():
    system, human = build_messages(KWARGS)

    assert isinstance(system, SystemMessage) and isinstance(human, HumanMessage)
    assert (
        system.content == load_skill_prompt("abbreviation-extraction") + CHUNK_GUIDANCE
    )
    content = str(human.content)
    assert "document lines 10-42" in content
    assert "10: line 10" in content and "42: line 42" in content
    assert "9: line 9" not in content and "43: line 43" not in content
    assert "/main.md" not in CHUNK_GUIDANCE
    assert "tools" in CHUNK_GUIDANCE


def test_guidance_leaves_document_wide_fields_to_deterministic_assembly():
    for field in ("abbr", "inline_definition", "line_start", "line_end"):
        assert f"`{field}`" in CHUNK_GUIDANCE
    assert "occurrence_number" not in CHUNK_GUIDANCE
    assert "abbreviations_section_definition" not in CHUNK_GUIDANCE


@pytest.mark.asyncio
async def test_one_structured_llm_call_returns_schema_and_trace_messages():
    found = ChunkExtractionResult(
        occurrences=[ChunkOccurrence(abbr="NATO", line_start=12, line_end=12)]
    )
    raw = AIMessage(content='{"occurrences": [{"abbr": "NATO"}]}')
    agent, model = _agent({"raw": raw, "parsed": found, "parsing_error": None})

    config = {"tags": ["test"]}
    result, messages = await agent.ainvoke(KWARGS, config=config)

    assert result == found
    assert model.schema is ChunkExtractionResult
    assert model.kwargs == {"include_raw": True}
    assert model.config == config
    assert len(model.messages) == 2
    assert [type(message) for message in messages] == [
        SystemMessage,
        HumanMessage,
        AIMessage,
    ]
    assert messages[-1] is raw


@pytest.mark.asyncio
async def test_truncated_response_raises_partial_with_salvaged_occurrences():
    complete = {
        "abbr": "NATO",
        "inline_definition": "",
        "line_start": 12,
        "line_end": 12,
    }
    raw = AIMessage(
        content='{"occurrences": [' + json.dumps(complete) + ', {"abbr": "EU", "inl'
    )
    parse_error = ValueError("cut")
    agent, _ = _agent({"raw": raw, "parsed": None, "parsing_error": parse_error})

    with pytest.raises(PartialChunkExtractionError) as excinfo:
        await agent.ainvoke(KWARGS)

    assert [occurrence.abbr for occurrence in excinfo.value.result.occurrences] == [
        "NATO"
    ]
    assert excinfo.value.__cause__ is parse_error
    assert excinfo.value.messages[-1] is raw


@pytest.mark.asyncio
async def test_unsalvageable_parse_error_is_reraised():
    error = ValueError("bad")
    agent, _ = _agent(
        {"raw": AIMessage(content="nope"), "parsed": None, "parsing_error": error}
    )

    with pytest.raises(ValueError, match="bad") as excinfo:
        await agent.ainvoke(KWARGS)

    assert excinfo.value is error
