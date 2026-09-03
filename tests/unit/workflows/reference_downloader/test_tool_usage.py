"""The per-reference log line is built from the agent transcript; pin what it counts."""

import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from lib.workflows.reference_downloader.tool_usage import summarize_tool_usage


def _download_result(success: bool) -> ToolMessage:
    payload = {
        "file_id": "f1" if success else None,
        "message": "Successfully downloaded" if success else "Failed to download",
        "success": success,
    }
    return ToolMessage(
        content=json.dumps(payload),
        name="download_file_from_url",
        tool_call_id="c1",
    )


def test_summary_counts_searches_downloads_and_reads():
    messages = [
        HumanMessage(content="ref"),
        AIMessage(
            content=[
                {
                    "type": "web_search_call",
                    "action": {"type": "search", "query": "q1"},
                },
                {
                    "type": "web_search_call",
                    "action": {"type": "open_page", "url": "u"},
                },
                {"type": "text", "text": "..."},
            ],
            response_metadata={"model_name": "gpt-5.6-terra-2026-07-09-global-aaif"},
        ),
        _download_result(success=False),
        _download_result(success=True),
        ToolMessage(content="text", name="read_file_content", tool_call_id="c2"),
        AIMessage(
            content="done",
            response_metadata={"model_name": "gpt-5.6-terra-2026-07-09-global-aaif"},
        ),
    ]

    summary = summarize_tool_usage(messages)

    assert summary.llm_calls == 2
    assert summary.model_names == ["gpt-5.6-terra-2026-07-09-global-aaif"]
    assert summary.web_searches == 1
    assert summary.pages_opened == 1
    assert summary.search_queries == ["q1"]
    assert summary.download_attempts == 2
    assert summary.download_successes == 1
    assert summary.download_failures == 1
    assert summary.reads == 1
    assert "web_searches=1" in summary.describe()
    assert "downloads=2 (ok=1 failed=1)" in summary.describe()


def test_summary_of_empty_transcript_is_all_zero():
    summary = summarize_tool_usage([])
    assert summary.llm_calls == 0
    assert "model=unknown" in summary.describe()


def test_non_json_download_result_falls_back_to_text_match():
    message = ToolMessage(
        content="Successfully downloaded content",
        name="download_file_from_url",
        tool_call_id="c",
    )
    assert summarize_tool_usage([message]).download_successes == 1
