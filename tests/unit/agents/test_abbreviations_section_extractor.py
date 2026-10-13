"""Tests for direct structured Abbreviations-section extraction."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from lib.agents.abbreviations_section_extractor import (
    MAX_RETRIES,
    REQUEST_TIMEOUT_SECONDS,
    AbbreviationsSectionExtraction,
    AbbreviationsSectionExtractorAgent,
    _numbered,
)
from lib.services.file_artifacts_service.file_artifacts_service_type import (
    FileArtifactsServiceType,
)
from lib.workflows.context import ContextSchema


def test_section_agent_fails_a_runaway_turn_early_and_retries_it_once() -> None:
    context = ContextSchema(
        openai_api_key="sk-test",
        file_artifacts_service=MagicMock(spec=FileArtifactsServiceType),
        project_id="test-project",
    )
    kwargs = AbbreviationsSectionExtractorAgent(context).get_init_chat_model_kwargs()
    assert kwargs["timeout"] == REQUEST_TIMEOUT_SECONDS < 240
    assert kwargs["max_retries"] == MAX_RETRIES == 1


class StubStructuredModel:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.schema: object = None
        self.kwargs: dict[str, Any] = {}
        self.calls = 0

    def with_structured_output(self, schema, **kwargs):
        self.schema = schema
        self.kwargs = kwargs
        return self

    async def ainvoke(self, messages, config=None):
        self.calls += 1
        self.messages = messages
        self.config = config
        return self.response


@pytest.mark.asyncio
async def test_section_extraction_is_one_structured_model_call() -> None:
    context = ContextSchema(
        project_id="p", file_artifacts_service=MagicMock(spec=FileArtifactsServiceType)
    )
    agent = AbbreviationsSectionExtractorAgent(context)
    extraction = AbbreviationsSectionExtraction()
    raw = AIMessage(content='{"sections": [], "entries": []}')
    model = StubStructuredModel(
        {"raw": raw, "parsed": extraction, "parsing_error": None}
    )
    agent._llm = model  # type: ignore[assignment]

    result, messages = await agent.ainvoke(
        {"markdown": "# Study\n## Abbreviations\nAI: artificial intelligence"},
        config={"tags": ["test"]},
    )

    assert result == extraction
    assert model.calls == 1
    assert model.schema is AbbreviationsSectionExtraction
    assert model.kwargs == {"include_raw": True}
    assert [type(message) for message in messages] == [
        SystemMessage,
        HumanMessage,
        AIMessage,
    ]
    assert "1: # Study" in str(messages[1].content)
    assert "3: AI: artificial intelligence" in str(messages[1].content)
    assert "/main.md" not in str(messages[0].content)


def test_numbered_preserves_blank_lines() -> None:
    assert _numbered("one\n\nthree") == "1: one\n2: \n3: three"
