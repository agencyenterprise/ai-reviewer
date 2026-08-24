"""Tests for how an HTML-report workflow gets its deliverable out of the agent.

The report used to come back as a JSON string in a structured response, and
that is what made `Extra data: line 1 column 14027` a way for a whole run to
fail: the model wrote a complete report object, kept talking, and the parse of
its final message took the run down with it. The report is now written to
`REPORT_PATH` with `write_file` and read off the agent filesystem.

Two things are worth holding still. The delivery mechanism, so the failure
cannot come back by someone re-adding a response schema. And the state, because
`DeepAgentResult.report_html` is what the generated frontend types expose and
what the UI renders -- the whole point of routing through the filesystem was to
leave that untouched.
"""

from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.workflows.models import WorkflowRunType
from lib.workflows.registry import get_workflow_manifest
from lib.workflows.simple_deep_agent.agent_types import (
    REPORT_PATH,
    AgentCheckResult,
    DeepAgentResult,
    DeepAgentRun,
    IssueItem,
    ReportNotWrittenError,
)
from lib.workflows.simple_deep_agent.agent import SimpleDeepAgent
from lib.workflows.simple_deep_agent.manifest_base import (
    HtmlReportDeepAgentManifest,
    SimpleDeepAgentManifest,
)
from lib.workflows.simple_deep_agent.state import SimpleDeepAgentState

# The three review-assistant outputs, all built on the HTML-report variant.
_HTML_WORKFLOWS = [
    WorkflowRunType.REVISION_PLANNING_SUMMARY,
    WorkflowRunType.REVIEWER_COVERAGE_REPORT,
    WorkflowRunType.REVIEWER_RESPONSE_MEMOS,
]

_REPORT = "<!doctype html><html><body><h1>Report</h1></body></html>"


def _stub_agent(response_model: Optional[type]) -> "SimpleDeepAgent":
    """A SimpleDeepAgent with its model and filesystem stubbed out."""
    context = MagicMock()
    context.file_artifacts_service.get_deepagent_backend_files = AsyncMock(
        return_value={}
    )
    agent = SimpleDeepAgent(
        context=context, user_prompt="rules", response_model=response_model
    )
    # Bypasses create_llm(), which would want an API key and a rate limiter.
    agent._llm = MagicMock()
    return agent


def _html_manifest() -> HtmlReportDeepAgentManifest:
    manifest = get_workflow_manifest(WorkflowRunType.REVISION_PLANNING_SUMMARY)
    assert isinstance(manifest, HtmlReportDeepAgentManifest)
    return manifest


# --- Delivery --------------------------------------------------------------


def test_report_is_read_from_the_agent_filesystem():
    run = DeepAgentRun(files={"/main.md": "# doc", REPORT_PATH: _REPORT})
    assert _html_manifest()._to_state_result(run).report_html == _REPORT


@pytest.mark.parametrize(
    "files",
    [
        pytest.param({}, id="no files at all"),
        pytest.param({"/main.md": "# doc"}, id="wrote nothing"),
        pytest.param({REPORT_PATH: ""}, id="empty report"),
        pytest.param({REPORT_PATH: "   \n  "}, id="whitespace only"),
        pytest.param({"/report.htm": _REPORT}, id="wrong path"),
    ],
)
def test_a_missing_report_fails_the_run(files: dict):
    """A run that produced nothing is a failure, not a blank deliverable.

    Returning an empty `report_html` would record the run as successful and
    hide it from both the UI and the evals, which score a missing report as a
    silent zero rather than an error.
    """
    with pytest.raises(ReportNotWrittenError) as caught:
        _html_manifest()._to_state_result(DeepAgentRun(files=files))
    assert REPORT_PATH in str(caught.value)


def test_the_final_message_cannot_influence_the_report():
    """The invariant that puts `Extra data` out of reach.

    Nothing the model says at the end is parsed, so a trailing second JSON
    object -- the shape of every failure observed in the eval logs -- has
    nowhere to do damage.
    """
    run = DeepAgentRun(
        files={REPORT_PATH: _REPORT},
        structured_response=AgentCheckResult(report_markdown="ignore me"),
    )
    result = _html_manifest()._to_state_result(run)
    assert result.report_html == _REPORT
    assert result.report_markdown == ""
    assert result.issues == []


# --- No structured output --------------------------------------------------


@pytest.mark.parametrize("workflow_type", _HTML_WORKFLOWS)
def test_html_workflows_declare_no_response_schema(workflow_type: WorkflowRunType):
    manifest = get_workflow_manifest(workflow_type)
    assert isinstance(manifest, HtmlReportDeepAgentManifest)
    assert manifest.result_model is None


@pytest.mark.parametrize("workflow_type", _HTML_WORKFLOWS)
def test_html_prompts_ask_for_a_file_write(workflow_type: WorkflowRunType):
    """The prompt has to name the path the node reads back, or nothing lands."""
    manifest = get_workflow_manifest(workflow_type)
    assert isinstance(manifest, HtmlReportDeepAgentManifest)
    prompt = manifest.system_prompt or ""
    assert REPORT_PATH in prompt
    assert "write_file" in prompt
    # The old instruction pointed at a schema field that no longer exists.
    assert "report_html" not in prompt


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response_model, expected",
    [
        pytest.param(None, None, id="no schema -> no response_format"),
        pytest.param(AgentCheckResult, AgentCheckResult, id="schema -> AutoStrategy"),
    ],
)
async def test_the_agent_only_constrains_output_when_asked(
    response_model: Optional[type], expected: Optional[type]
):
    """`response_format=None` is what takes the failing parse off the table."""
    agent = _stub_agent(response_model)

    with patch(
        "lib.workflows.simple_deep_agent.agent.create_deep_agent"
    ) as create_agent:
        create_agent.return_value.ainvoke = AsyncMock(
            return_value={"messages": [], "files": {}, "structured_response": None}
        )
        await agent.ainvoke({})

    fmt = create_agent.call_args.kwargs["response_format"]
    assert (fmt.schema if fmt is not None else None) is expected


@pytest.mark.asyncio
async def test_the_agent_returns_the_filesystem_as_text():
    """deepagents stores files as lines; the run hands back whole strings."""
    agent = _stub_agent(None)

    with patch(
        "lib.workflows.simple_deep_agent.agent.create_deep_agent"
    ) as create_agent:
        create_agent.return_value.ainvoke = AsyncMock(
            return_value={
                "messages": [],
                "structured_response": None,
                "files": {REPORT_PATH: {"content": ["<html>", "<body>", "</html>"]}},
            }
        )
        run = await agent.ainvoke({})

    assert run.files == {REPORT_PATH: "<html>\n<body>\n</html>"}


# --- The state contract the frontend reads ---------------------------------


def test_state_result_shape_is_unchanged():
    """`DeepAgentResult` is the generated frontend type; its fields are a contract.

    `frontend/lib/generated-api/types.gen.ts` exposes `report_html?: string` off
    this model and `simple-deep-agent-results.tsx` renders it. Adding, renaming
    or dropping a field here means regenerating the API types and touching the
    frontend, which moving the report to a file was meant to avoid.
    """
    assert set(DeepAgentResult.model_fields) == {
        "issues",
        "report_markdown",
        "report_html",
    }
    assert set(SimpleDeepAgentState.model_fields) >= {
        "type",
        "config",
        "result",
        "messages",
    }


def test_the_markdown_variant_still_uses_its_schema():
    """The validation workflows are untouched: they need issues with line numbers."""
    assert SimpleDeepAgentManifest.result_model is AgentCheckResult

    manifest = get_workflow_manifest(WorkflowRunType.FIGURES_TABLES_CHECK)
    assert isinstance(manifest, SimpleDeepAgentManifest)
    run = DeepAgentRun(
        structured_response=AgentCheckResult(
            issues=[IssueItem(title="t", description="d", start_line=1, end_line=2)],
            report_markdown="# summary",
        )
    )
    result = manifest._to_state_result(run)
    assert result.report_markdown == "# summary"
    assert [i.title for i in result.issues] == ["t"]
    assert result.report_html == ""
