"""Recover usable records from a truncated structured-output response.

A provider can end a response mid-JSON: OpenAI reports `status: "incomplete"`
with an `incomplete_details.reason` of `max_output_tokens` or `content_filter`.
LangChain's native structured-output binding then calls `json.loads` on the
partial text and raises, so one cut-off response discards every record the model
had already finished writing.

These helpers read the complete items out of the fragment instead. Each item is
decoded by the real JSON parser, so a salvaged record is exactly what the model
emitted — only the record that was mid-write when the response stopped, and
anything that would have followed it, is lost.
"""

import json
import logging
import re
from typing import Any, List, Type, TypeVar

from langchain_core.messages import AIMessage
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)

_DECODER = json.JSONDecoder()
_SEPARATORS = " \t\r\n,"


def ai_message_text(message: AIMessage) -> str:
    """Concatenate the text content of an `AIMessage`, ignoring other blocks."""
    content = message.content
    if isinstance(content, str):
        return content

    parts: List[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "".join(parts)


def salvage_list_items(raw_text: str, key: str) -> List[Any]:
    """Decode the complete items of `raw_text`'s `key` array.

    Returns every element that parses, stopping at the first one that does not
    (the truncation point). Returns an empty list when the key is absent or no
    element completed. Matches the first occurrence of the key, so a document
    whose earlier string content happens to contain `"<key>": [` is not handled.
    """
    match = re.search(rf'"{re.escape(key)}"\s*:\s*\[', raw_text)
    if not match:
        return []

    items: List[Any] = []
    index = match.end()
    while index < len(raw_text):
        while index < len(raw_text) and raw_text[index] in _SEPARATORS:
            index += 1
        if index >= len(raw_text) or raw_text[index] == "]":
            break
        try:
            item, index = _DECODER.raw_decode(raw_text, index)
        except ValueError:
            break
        items.append(item)

    return items


def salvage_models(raw_text: str, key: str, model: Type[ModelT]) -> List[ModelT]:
    """Salvage `key`'s array items and validate each into `model`.

    Items that fail validation are dropped: a truncated response can end with a
    syntactically complete object that is missing required fields.
    """
    salvaged: List[ModelT] = []
    for item in salvage_list_items(raw_text, key):
        try:
            salvaged.append(model.model_validate(item))
        except ValidationError as e:
            logger.debug("Discarding unusable salvaged %s: %s", model.__name__, e)
    return salvaged
