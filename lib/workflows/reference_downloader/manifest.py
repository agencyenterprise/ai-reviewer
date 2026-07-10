from typing import List, Type

from langgraph.graph import StateGraph

from lib.workflows.manifest import WorkflowManifest
from lib.workflows.models import DocumentIssue, WorkflowRunType
from lib.workflows.reference_downloader.graph import build_reference_downloader_graph
from lib.workflows.reference_downloader.state import (
    ReferenceDownloaderState,
    ReferenceDownloaderWorkflowConfig,
    ReferenceFetchStatus,
)
from lib.workflows.workflow_types import WorkflowState


class ReferenceDownloaderManifest(
    WorkflowManifest[ReferenceDownloaderState, ReferenceDownloaderWorkflowConfig]
):
    type = WorkflowRunType.REFERENCE_DOWNLOADER
    name = "Reference Downloader"
    description = "Search the web for each reference and download the related full-text when available (PDF or Markdown)."
    needs_web_search = True
    is_internal = True
    # Required so callers triggering this workflow without an explicit
    # `references` list (e.g. via /api/workflows/start-multiple or MCP) have
    # the upstream extraction available to derive the default "all unmatched"
    # reference set. File matching is only optional — it doesn't have to have
    # run, but if it is currently running we wait so the unmatched set is
    # accurate.
    required_dependencies = [WorkflowRunType.REFERENCE_EXTRACTION]
    optional_dependencies = [WorkflowRunType.REFERENCE_FILE_MATCHING]

    def get_state_type(self) -> Type[ReferenceDownloaderState]:
        """Get the type of the workflow state."""
        return ReferenceDownloaderState

    def get_config_type(self) -> Type[ReferenceDownloaderWorkflowConfig]:
        """Get the type of the workflow config."""
        return ReferenceDownloaderWorkflowConfig

    def build_graph(self) -> StateGraph:
        """Build and return the graph of the workflow."""
        return build_reference_downloader_graph()

    async def on_cancel(
        self, state: ReferenceDownloaderState
    ) -> ReferenceDownloaderState:
        """Mark any pending reference fetches as cancelled so they don't show as in-progress."""
        updated = [
            (
                item.model_copy(update={"status": ReferenceFetchStatus.CANCELLED})
                if item.status == ReferenceFetchStatus.PENDING
                else item
            )
            for item in state.fetched_references
        ]
        return state.model_copy(update={"fetched_references": updated})

    async def create_initial_state(
        self,
        config: ReferenceDownloaderWorkflowConfig,
        existing_states: List[WorkflowState],
        revision: int,
        prior_self_state: ReferenceDownloaderState | None = None,
    ) -> ReferenceDownloaderState:
        """Create and return the initial state of the workflow.

        Seeds fetched_references from the prior run's state so already-fetched
        references carry forward. Threads are no longer reused across runs, so
        this state is no longer inherited via the checkpointer.
        """
        fetched_references = (
            prior_self_state.fetched_references if prior_self_state is not None else []
        )
        return ReferenceDownloaderState(
            type=WorkflowRunType.REFERENCE_DOWNLOADER,
            config=config,
            fetched_references=fetched_references,
        )

    def convert_state_to_issues(
        self,
        state: ReferenceDownloaderState,
        other_states: List[WorkflowState],
    ) -> List[DocumentIssue]:
        """Convert ReferenceDownloaderState to issues."""
        return []
