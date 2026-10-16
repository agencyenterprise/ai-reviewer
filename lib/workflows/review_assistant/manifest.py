"""Manifest for the Review Assistant workflow.

The way into the `review-assistant` skill. The author picks the
outputs they want and hands over every document they have (drafts, reviewer
memos, marked-up copies, response memos) without saying which is which. One
agent run works out what each document is, builds the skill's shared
foundation once, and writes one HTML report per requested output, so the point
IDs line up across all of them.

Nothing here depends on the project's revisions: the documents are exactly
the files named in the run's config, and Word comments and tracked changes are
mounted beside each document's text (see ``inputs.py``).
"""

import builtins
import json
import logging
from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from lib.services.file_artifacts_service.file_artifacts_service import (
    skill_backend_files,
)
from lib.services.file_artifacts_service.file_artifacts_service_type import (
    UnreadableDocument,
)
from lib.skills import load_skill_prompt
from lib.workflows.context import ContextSchema
from lib.workflows.decorators import register_node
from lib.workflows.manifest import WorkflowManifest
from lib.workflows.models import (
    DocumentIssue,
    WorkflowError,
    WorkflowErrorSeverity,
    WorkflowRunType,
)
from lib.workflows.review_assistant.inputs import mount_review_inputs
from lib.workflows.review_assistant.prompt import (
    INPUT_READINGS_PATH,
    REPORT_PATHS,
    build_system_prompt,
)
from lib.workflows.review_assistant.state import (
    ReviewAssistantConfig,
    ReviewAssistantInputReading,
    ReviewAssistantReport,
    ReviewAssistantState,
)
from lib.workflows.simple_deep_agent.agent import SimpleDeepAgent
from lib.workflows.simple_deep_agent.agent_types import (
    DeepAgentRun,
    ReportNotWrittenError,
)

if TYPE_CHECKING:
    from lib.workflows.workflow_types import WorkflowState

logger = logging.getLogger(__name__)

SKILL = "review-assistant"


def collect_reports(
    run: DeepAgentRun, state: ReviewAssistantState
) -> list[ReviewAssistantReport]:
    """The reports the agent wrote, in the order they were asked for.

    An output it did not write is left out rather than failing the others; a
    run that wrote none of them failed.
    """
    reports = [
        ReviewAssistantReport(output=output, report_html=html)
        for output in state.config.outputs
        if (html := run.files.get(REPORT_PATHS[output], "").strip())
    ]
    if not reports:
        raise ReportNotWrittenError(
            REPORT_PATHS[state.config.outputs[0]], list(run.files)
        )
    return reports


def read_input_readings(run: DeepAgentRun) -> list[ReviewAssistantInputReading]:
    """What the agent said each document is. Advisory, so a missing or
    malformed file costs only this list."""
    raw = run.files.get(INPUT_READINGS_PATH)
    if not raw:
        return []
    try:
        entries = json.loads(raw)
        readings = [ReviewAssistantInputReading.model_validate(e) for e in entries]
    except (ValueError, TypeError) as error:
        logger.warning("Ignoring unreadable %s: %s", INPUT_READINGS_PATH, error)
        return []
    # The UI matches readings to inputs by folder, and a folder copied with a
    # trailing slash would match nothing.
    for reading in readings:
        reading.folder = reading.folder.rstrip("/")
    return readings


def unreadable_document_warning(
    item: UnreadableDocument, workflow_run_id: str | None
) -> WorkflowError:
    """A warning that the run went ahead without one document.

    A warning rather than an error: the outputs are still real, they just did
    not read this file, and the request view lists it so the author can retry.
    """
    return WorkflowError(
        task_name="read_documents",
        error=f"Could not read {item.file_name}, so this request ran without it: {item.reason}",
        workflow_run_id=workflow_run_id,
        severity=WorkflowErrorSeverity.WARNING,
    )


def markup_not_read_warning(reason: str, workflow_run_id: str | None) -> WorkflowError:
    """A warning that a document's comments and tracked changes were not read.

    Its text was, but a reviewer who marked up a copy may have left their
    feedback only there, so the outputs may be missing it.
    """
    return WorkflowError(
        task_name="read_documents",
        error=f"{reason} Feedback left only as comments or tracked changes is missing.",
        workflow_run_id=workflow_run_id,
        severity=WorkflowErrorSeverity.WARNING,
    )


# The request endpoint requires both, so a run that lacks either was started
# through the generic workflow start, which cannot name them.
_NEEDS_A_REQUEST = (
    "A Review Assistant run needs a request naming its outputs and documents. "
    "Start one from the project's Review Assistant tab, or with "
    "POST /api/project/{project_id}/review-assistant/requests."
)


def precheck(config: ReviewAssistantConfig) -> str | None:
    if not config.outputs or not config.input_file_ids:
        return _NEEDS_A_REQUEST.format(project_id=config.project_id)
    return None


class ReviewAssistantManifest(
    WorkflowManifest[ReviewAssistantState, ReviewAssistantConfig]
):
    type = WorkflowRunType.REVIEW_ASSISTANT
    name = "Review Assistant"
    description = (
        "Produces any of the review-assistant outputs (revision-planning summary, "
        "reviewer response memos, reviewer coverage report) from whatever documents "
        "the author has, unlabeled: drafts, reviewer memos, Word copies with "
        "comments and tracked changes, and response memos."
    )
    is_experimental = True
    # Started only from the Review Assistant tab, with the documents it names.
    auto_rerun_on_new_revision = False
    # A request reads the files it names, so a new revision leaves it running,
    # and a second request need not wait up to two hours for the first.
    independent_runs = True
    # Up to three long deliverables from one agent.
    max_duration_seconds = 2 * 60 * 60

    def get_state_type(self) -> builtins.type[ReviewAssistantState]:
        return ReviewAssistantState

    def get_config_type(self) -> builtins.type[ReviewAssistantConfig]:
        return ReviewAssistantConfig

    def build_graph(self) -> StateGraph:
        async def run_agent(
            state: ReviewAssistantState, runtime: Runtime[ContextSchema]
        ) -> dict:
            guard = precheck(state.config)
            if guard is not None:
                return {"guard_message": guard}
            service = runtime.context.file_artifacts_service
            loaded = await service.get_file_documents(state.config.input_file_ids)
            errors = [
                unreadable_document_warning(item, runtime.context.workflow_run_id)
                for item in loaded.unreadable
            ]
            if not loaded.documents:
                return {
                    "guard_message": "None of the chosen documents could be read.",
                    "errors": errors,
                }

            mounted = await mount_review_inputs(loaded.documents)
            errors.extend(
                markup_not_read_warning(reason, runtime.context.workflow_run_id)
                for reason in mounted.markup_warnings
            )
            agent = SimpleDeepAgent(
                context=runtime.context,
                system_prompt=build_system_prompt(state.config.outputs),
                user_prompt=load_skill_prompt(SKILL),
                report_issues=False,
                reasoning_effort="high",
                backend_files={**mounted.files, **skill_backend_files()},
            )
            run = await agent.ainvoke({})
            return {
                "inputs": mounted.inputs,
                "input_readings": read_input_readings(run),
                "reports": collect_reports(run, state),
                "messages": run.messages,
                "errors": errors,
            }

        graph = StateGraph(ReviewAssistantState, context_schema=ContextSchema)
        graph.add_node("run_agent", register_node(self.name)(run_agent))
        graph.add_edge(START, "run_agent")
        graph.add_edge("run_agent", END)
        return graph  # type: ignore[return-value]

    async def create_initial_state(
        self,
        config: ReviewAssistantConfig,
        existing_states: list["WorkflowState"],
        revision: int,
        prior_self_state: ReviewAssistantState | None = None,
    ) -> ReviewAssistantState:
        return ReviewAssistantState(config=config)

    def convert_state_to_issues(
        self, state: ReviewAssistantState, other_states: list["WorkflowState"]
    ) -> list[DocumentIssue]:
        return []
