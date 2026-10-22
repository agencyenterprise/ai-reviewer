"""Manifest for abbreviation scan v2 workflow."""

from langgraph.graph import StateGraph

from lib.workflows.abbreviation_scan_v2.chunk_models import ChunkStatus
from lib.workflows.abbreviation_scan_v2.graph import build_abbreviation_scan_v2_graph
from lib.workflows.abbreviation_scan_v2.issues import build_issues
from lib.workflows.abbreviation_scan_v2.state import (
    AbbreviationScanV2Config,
    AbbreviationScanV2State,
)
from lib.workflows.manifest import WorkflowManifest
from lib.workflows.models import DocumentIssue, WorkflowRunType
from lib.workflows.reducers import cancel_pending
from lib.workflows.workflow_types import WorkflowState


class AbbreviationScanV2Manifest(
    WorkflowManifest[AbbreviationScanV2State, AbbreviationScanV2Config]
):
    type = WorkflowRunType.ABBREVIATION_SCAN_V2
    name = "Abbreviation Scan"
    description = "Have you defined all abbreviations and acronyms accurately and consistently? Checks that every abbreviation is spelled out at first use and all abbreviations are listed in an Abbreviations section."
    needs_web_search = False
    is_internal = False
    is_experimental = False
    required_dependencies = [WorkflowRunType.DOCUMENT_PROCESSING]

    def build_graph(self) -> StateGraph:
        return build_abbreviation_scan_v2_graph()

    async def on_cancel(
        self, state: AbbreviationScanV2State
    ) -> AbbreviationScanV2State:
        """Mark any pending chunks as cancelled so they don't show as in-progress."""
        updated = cancel_pending(
            state.chunks, ChunkStatus.PENDING, ChunkStatus.CANCELLED
        )
        return state.model_copy(update={"chunks": updated})

    def convert_state_to_issues(
        self, state: AbbreviationScanV2State, other_states: list[WorkflowState]
    ) -> list[DocumentIssue]:
        return build_issues(state)
