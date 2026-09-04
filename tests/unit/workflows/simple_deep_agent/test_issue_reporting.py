"""Unit tests for the per-invocation issue-reporting tools."""

from concurrent.futures import ThreadPoolExecutor

from langchain_core.messages import AIMessage, ToolMessage

from lib.workflows.simple_deep_agent.issue_reporting import (
    IssueReporter,
    collect_deep_agent_run,
)


def _tools(reporter: IssueReporter) -> dict:
    return {tool.name: tool for tool in reporter.tools}


def _issue(title: str = "Missing section") -> dict:
    return {
        "title": title,
        "description": "The required section was not found.",
        "severity": "high",
        "start_line": 1,
        "end_line": 1,
        "suggested_action": "Add the required section.",
    }


def test_report_issue_collects_a_typed_issue():
    reporter = IssueReporter()
    tools = _tools(reporter)

    confirmation = tools["report_issue"].invoke(_issue())

    assert confirmation.startswith("Recorded issue-1")
    assert [issue.title for issue in reporter.issues] == ["Missing section"]


def test_tool_description_is_document_path_agnostic():
    description = _tools(IssueReporter())["report_issue"].description
    assert "document under review" in description
    assert "/main.md" not in description


def test_invalid_line_ranges_and_blank_fields_are_not_recorded():
    reporter = IssueReporter()
    report_issue = _tools(reporter)["report_issue"]

    for overrides in (
        {"title": ""},
        {"description": "  "},
        {"start_line": 0},
        {"start_line": 5, "end_line": 4},
    ):
        result = report_issue.invoke({**_issue(), **overrides})
        assert result.startswith("Issue was not recorded:")

    assert reporter.issues == []


def test_exact_duplicate_calls_are_suppressed():
    reporter = IssueReporter()
    report_issue = _tools(reporter)["report_issue"]

    assert report_issue.invoke(_issue()).startswith("Recorded issue-1")
    assert "duplicate ignored" in report_issue.invoke(_issue())
    assert len(reporter.issues) == 1


def test_collectors_are_isolated_and_safe_for_parallel_calls():
    first = IssueReporter()
    second = IssueReporter()
    first_tool = _tools(first)["report_issue"]
    second_tool = _tools(second)["report_issue"]

    calls = [(first_tool, _issue(f"First {index}")) for index in range(10)] + [
        (second_tool, _issue(f"Second {index}")) for index in range(10)
    ]
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda call: call[0].invoke(call[1]), calls))

    assert {issue.title for issue in first.issues} == {
        f"First {index}" for index in range(10)
    }
    assert {issue.title for issue in second.issues} == {
        f"Second {index}" for index in range(10)
    }


def test_collected_run_does_not_carry_viewed_image_bytes():
    """Run messages are persisted as the workflow's state_json and served with
    the run detail, so a viewed image must be reduced to a note there."""
    image_result = ToolMessage(
        content=[{"type": "image", "data": "QUJDRA==", "mime_type": "image/png"}],
        tool_call_id="call-1",
        name="view_image",
    )
    run = collect_deep_agent_run(
        {"files": {}, "messages": [AIMessage(content="done"), image_result]}
    )

    assert "QUJDRA==" not in str(run.messages)
    assert "image/png" in str(run.messages[1].content)
