"""Summarise what a reference-fetch agent run actually did, for the logs.

A reference that ends as "not found" looks identical in the log whether the model
never searched, searched and found nothing, or found a URL that the download tool
could not fetch. This module reads the agent transcript back and counts each kind of
step, so a single INFO line per reference can tell those cases apart.
"""

import json
from typing import Any, Sequence

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from pydantic import BaseModel, Field

DOWNLOAD_TOOL_NAME = "download_file_from_url"
READ_TOOL_NAME = "read_file_content"
MAX_LOGGED_QUERIES = 8


class ToolUsageSummary(BaseModel):
    llm_calls: int = 0
    model_names: list[str] = Field(default_factory=list)
    web_searches: int = 0
    pages_opened: int = 0
    search_queries: list[str] = Field(default_factory=list)
    download_attempts: int = 0
    download_successes: int = 0
    download_failures: int = 0
    reads: int = 0

    def describe(self) -> str:
        """One line, grep-friendly, for the per-reference log record."""
        queries = "; ".join(
            q.replace("\n", " ") for q in self.search_queries[:MAX_LOGGED_QUERIES]
        )
        models = ",".join(self.model_names) or "unknown"
        return (
            f"llm_calls={self.llm_calls} model={models} "
            f"web_searches={self.web_searches} pages_opened={self.pages_opened} "
            f"downloads={self.download_attempts} "
            f"(ok={self.download_successes} failed={self.download_failures}) "
            f"reads={self.reads} queries=[{queries}]"
        )


def summarize_tool_usage(messages: Sequence[BaseMessage | dict]) -> ToolUsageSummary:
    summary = ToolUsageSummary()
    for message in messages:
        if isinstance(message, AIMessage):
            _count_ai_message(message, summary)
        elif isinstance(message, ToolMessage):
            _count_tool_message(message, summary)
    return summary


def _count_ai_message(message: AIMessage, summary: ToolUsageSummary) -> None:
    summary.llm_calls += 1
    model_name = message.response_metadata.get(
        "model_name"
    ) or message.response_metadata.get("model")
    if model_name and model_name not in summary.model_names:
        summary.model_names.append(str(model_name))
    if not isinstance(message.content, list):
        return
    for block in message.content:
        if isinstance(block, dict) and block.get("type") == "web_search_call":
            _count_web_search_call(block, summary)


def _count_web_search_call(block: dict[str, Any], summary: ToolUsageSummary) -> None:
    action = block.get("action") or {}
    action_type = action.get("type") if isinstance(action, dict) else None
    if action_type == "open_page":
        summary.pages_opened += 1
        return
    summary.web_searches += 1
    query = action.get("query") if isinstance(action, dict) else None
    if query:
        summary.search_queries.append(str(query))


def _count_tool_message(message: ToolMessage, summary: ToolUsageSummary) -> None:
    if message.name == READ_TOOL_NAME:
        summary.reads += 1
        return
    if message.name != DOWNLOAD_TOOL_NAME:
        return
    summary.download_attempts += 1
    if _download_succeeded(message.content):
        summary.download_successes += 1
    else:
        summary.download_failures += 1


def _download_succeeded(content: Any) -> bool:
    """The download tool returns `DownloadFileFromUrlResponse` as JSON."""
    if not isinstance(content, str):
        return False
    try:
        payload = json.loads(content)
    except ValueError:
        return "Successfully downloaded" in content
    return isinstance(payload, dict) and bool(payload.get("success"))
