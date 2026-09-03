"""Per-run tools for collecting document issues from a deep agent.

Issue reporting is an ordinary tool interaction rather than the agent's terminal
structured response. Each agent invocation owns one collector, so calls from
concurrent workflow runs cannot share state. The agent explicitly completes the
report by writing `/report.md`; zero issue-tool calls means no issues were found.
"""

from threading import Lock
from typing import Any, List, Literal, Optional

from deepagents.backends.utils import file_data_to_string
from langchain_core.tools import BaseTool, tool

from lib.agents.tools.view_image import redact_image_blocks
from lib.workflows.simple_deep_agent.agent_types import DeepAgentRun, IssueItem


class IssueReporter:
    """Collect validated issues through tools scoped to one agent invocation."""

    def __init__(self) -> None:
        self._issues: List[IssueItem] = []
        self._issue_ids: dict[str, str] = {}
        self._lock = Lock()
        self.tools = [self._build_report_tool()]

    @property
    def issues(self) -> List[IssueItem]:
        """Return a snapshot so callers cannot mutate the collector."""
        with self._lock:
            return list(self._issues)

    def _build_report_tool(self) -> BaseTool:
        reporter = self

        @tool()
        def report_issue(
            title: str,
            description: str,
            severity: Literal["none", "low", "medium", "high"],
            start_line: int,
            end_line: int,
            long_description: Optional[str] = None,
            suggested_action: Optional[str] = None,
        ) -> str:
            """Report one verified issue in the document under review.

            Call this exactly once for each genuine issue after checking it
            against the document under review. Do not call it for passing rules
            unless the workflow explicitly requests an informational issue with
            severity `none`. If a call is rejected, correct the arguments and
            try again.

            Args:
                title: Short, specific issue title.
                description: Concise markdown explanation grounded in the document.
                severity: Impact level: none, low, medium, or high.
                start_line: 1-indexed first relevant line in the document.
                end_line: 1-indexed last relevant line; not before start_line.
                long_description: Optional extended markdown detail.
                suggested_action: Optional direct recommendation for the author.

            Returns:
                A confirmation containing the recorded issue identifier, or a
                correction message when the issue was not recorded.
            """
            if not title.strip():
                return "Issue was not recorded: title must not be blank."
            if not description.strip():
                return "Issue was not recorded: description must not be blank."
            if start_line < 1:
                return "Issue was not recorded: start_line must be at least 1."
            if end_line < start_line:
                return (
                    "Issue was not recorded: end_line must be greater than or "
                    "equal to start_line."
                )

            issue = IssueItem(
                title=title,
                description=description,
                severity=severity,
                start_line=start_line,
                end_line=end_line,
                long_description=long_description,
                suggested_action=suggested_action,
            )
            fingerprint = issue.model_dump_json(exclude_none=False)

            with reporter._lock:
                existing_id = reporter._issue_ids.get(fingerprint)
                if existing_id is not None:
                    return (
                        f"Issue already recorded as {existing_id}; duplicate ignored."
                    )

                issue_id = f"issue-{len(reporter._issues) + 1}"
                reporter._issues.append(issue)
                reporter._issue_ids[fingerprint] = issue_id
                return f"Recorded {issue_id}: {issue.title}"

        return report_issue


def collect_deep_agent_run(
    result: dict[str, Any], issue_reporter: Optional[IssueReporter] = None
) -> DeepAgentRun:
    """Convert a raw DeepAgents result and optional collector into one run."""
    return DeepAgentRun(
        files={
            path: file_data_to_string(data)
            for path, data in (result.get("files") or {}).items()
        },
        reported_issues=issue_reporter.issues if issue_reporter else [],
        # Viewed images are base64 in the tool results; keep the transcript
        # readable and the persisted state small.
        messages=redact_image_blocks(result["messages"]),
    )
