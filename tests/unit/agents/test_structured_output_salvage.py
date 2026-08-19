"""Tests for recovering records from a truncated structured-output response."""

from __future__ import annotations

from typing import List, Optional

from langchain_core.messages import AIMessage
from pydantic import BaseModel

from lib.agents.structured_output_salvage import (
    ai_message_text,
    salvage_list_items,
    salvage_models,
)


class _Assessment(BaseModel):
    quoted_text: str
    line_start: int
    rationale: str = ""
    tags: List[str] = []
    mapping: Optional[str] = None


def test_recovers_complete_items_before_the_cut():
    truncated = (
        '{"issues":[{"quoted_text":"first","line_start":1},'
        '{"quoted_text":"second","line_start":2},'
        '{"quoted_text":"third, cut mid-str'
    )

    items = salvage_list_items(truncated, "issues")

    assert [item["quoted_text"] for item in items] == ["first", "second"]


def test_returns_every_item_of_a_complete_array():
    complete = '{"issues":[{"quoted_text":"a","line_start":1},{"quoted_text":"b","line_start":2}]}'

    assert len(salvage_list_items(complete, "issues")) == 2


def test_returns_empty_when_the_key_is_absent():
    assert salvage_list_items('{"other":[{"a":1}]}', "issues") == []
    assert salvage_list_items("", "issues") == []


def test_returns_empty_when_the_first_item_is_incomplete():
    assert salvage_list_items('{"issues":[{"quoted_text":"cut', "issues") == []


def test_handles_an_empty_array():
    assert salvage_list_items('{"issues":[]}', "issues") == []


def test_string_content_does_not_confuse_the_scanner():
    """Braces, brackets, commas and escaped quotes inside strings are data."""
    truncated = (
        '{"issues":[{"quoted_text":"a }] , \\"quoted\\" [brace}","line_start":1},'
        '{"quoted_text":"partial'
    )

    items = salvage_list_items(truncated, "issues")

    assert len(items) == 1
    assert items[0]["quoted_text"] == 'a }] , "quoted" [brace}'


def test_handles_nested_objects_and_arrays():
    truncated = (
        '{"issues":[{"quoted_text":"a","line_start":1,'
        '"evidence_sources":[{"quote":"q","file_id":"f"}]},'
        '{"quoted_text":"b","line_start":2,"evidence_sources":[{"quote":"cut'
    )

    items = salvage_list_items(truncated, "issues")

    assert len(items) == 1
    assert items[0]["evidence_sources"][0]["file_id"] == "f"


def test_tolerates_whitespace_and_pretty_printing():
    truncated = """{
      "issues": [
        { "quoted_text": "a", "line_start": 1 },
        { "quoted_text": "b", "line_start": 2 },
        { "quoted_text": "c"
    """

    assert len(salvage_list_items(truncated, "issues")) == 2


def test_salvage_models_validates_and_drops_unusable_items():
    """A complete object can still be missing required fields."""
    truncated = (
        '{"issues":[{"quoted_text":"a","line_start":1},'
        '{"quoted_text":"missing line_start"},'
        '{"quoted_text":"c","line_start":3},'
        '{"quoted_text":"cut'
    )

    salvaged = salvage_models(truncated, "issues", _Assessment)

    assert [item.quoted_text for item in salvaged] == ["a", "c"]
    assert all(isinstance(item, _Assessment) for item in salvaged)


def test_ai_message_text_reads_plain_and_block_content():
    assert ai_message_text(AIMessage(content="plain")) == "plain"

    blocks = AIMessage(
        content=[
            {"type": "reasoning", "summary": "ignored"},
            {"type": "text", "text": '{"issues":['},
            {"type": "text", "text": '{"quoted_text":"a"}]}'},
        ]
    )
    assert ai_message_text(blocks) == '{"issues":[{"quoted_text":"a"}]}'
