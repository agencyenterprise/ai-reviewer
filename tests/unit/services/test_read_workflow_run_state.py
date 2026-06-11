"""Unit tests for the read_workflow_run_state chokepoint (RANDZ-561 PR 2).

The original History UI bug was that re-runs of a workflow type reused a single
langgraph_thread_id, so reading per-run state from the checkpointer returned the
*same* (latest) thread state for every run. Reading from each row's own
state_json fixes this: two runs that share a thread_id but carry distinct
state_json must hydrate to distinct states.
"""

import uuid

import pytest

from lib.models.workflow_run import WorkflowRun, WorkflowRunStatus
from lib.services.workflow_runs import read_workflow_run_state
from lib.workflows.models import WorkflowRunType
from lib.workflows.reference_file_matching.state import (
    ReferenceFileMatch,
    ReferenceFileMatchingConfig,
    ReferenceFileMatchingState,
    MatchSource,
)


def _make_state(file_id: str, reference_id: str) -> ReferenceFileMatchingState:
    return ReferenceFileMatchingState(
        type=WorkflowRunType.REFERENCE_FILE_MATCHING,
        config=ReferenceFileMatchingConfig(project_id=str(uuid.uuid4())),
        file_id=file_id,
        supporting_file_ids=[],
        matches=[
            ReferenceFileMatch(
                reference_id=reference_id,
                file_id=file_id,
                source=MatchSource.AUTO_MATCHED,
            )
        ],
    )


def _make_run(thread_id: str, state: ReferenceFileMatchingState) -> WorkflowRun:
    return WorkflowRun(
        id=uuid.uuid4(),
        langgraph_thread_id=thread_id,
        project_id=None,
        type=WorkflowRunType.REFERENCE_FILE_MATCHING,
        status=WorkflowRunStatus.COMPLETED,
        state_json=state.model_dump(mode="json"),
    )


@pytest.mark.asyncio
async def test_reads_each_runs_own_state_despite_shared_thread_id():
    shared_thread = str(uuid.uuid4())
    state_a = _make_state(file_id="file-a", reference_id="ref-a")
    state_b = _make_state(file_id="file-b", reference_id="ref-b")
    run_a = _make_run(shared_thread, state_a)
    run_b = _make_run(shared_thread, state_b)

    hydrated_a = await read_workflow_run_state(run_a)
    hydrated_b = await read_workflow_run_state(run_b)

    assert isinstance(hydrated_a, ReferenceFileMatchingState)
    assert isinstance(hydrated_b, ReferenceFileMatchingState)
    # Each run hydrates to its OWN state, not the shared thread's latest.
    assert hydrated_a.file_id == "file-a"
    assert hydrated_b.file_id == "file-b"


@pytest.mark.asyncio
async def test_returns_none_when_state_json_missing():
    run = WorkflowRun(
        id=uuid.uuid4(),
        langgraph_thread_id=str(uuid.uuid4()),
        project_id=None,
        type=WorkflowRunType.REFERENCE_FILE_MATCHING,
        status=WorkflowRunStatus.COMPLETED,
        state_json=None,
    )

    assert await read_workflow_run_state(run) is None
