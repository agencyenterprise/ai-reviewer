"""Unit tests for remove_file_from_references service function."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.services.references import remove_file_from_references
from lib.workflows.reference_file_matching.state import (
    MatchSource,
    ReferenceFileMatch,
    ReferenceFileMatchingConfig,
    ReferenceFileMatchingState,
)
from lib.workflows.models import WorkflowRunType


def _make_state(matches: list[ReferenceFileMatch]) -> ReferenceFileMatchingState:
    return ReferenceFileMatchingState(
        type=WorkflowRunType.REFERENCE_FILE_MATCHING,
        config=ReferenceFileMatchingConfig(project_id=str(uuid.uuid4())),
        file_id=str(uuid.uuid4()),
        supporting_file_ids=[],
        matches=matches,
    )


def _make_run() -> MagicMock:
    run = MagicMock()
    run.id = str(uuid.uuid4())
    run.langgraph_thread_id = str(uuid.uuid4())
    return run


@pytest.fixture(autouse=True)
def _stub_persist_state():
    """Capture the state_json write; the checkpointer write was removed in the
    write-side cutover, so persist_workflow_run_state is now the only write."""
    with patch(
        "lib.services.references.persist_workflow_run_state", new=AsyncMock()
    ) as m:
        yield m


@pytest.mark.asyncio
async def test_returns_empty_when_no_workflow_run(_stub_persist_state):
    with patch(
        "lib.services.references._get_file_matching_workflow_state",
        new=AsyncMock(return_value=(None, None)),
    ):
        removed = await remove_file_from_references(
            str(uuid.uuid4()), str(uuid.uuid4()), revision=1
        )

    assert removed == []
    _stub_persist_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_returns_empty_when_no_state(_stub_persist_state):
    with patch(
        "lib.services.references._get_file_matching_workflow_state",
        new=AsyncMock(return_value=(_make_run(), None)),
    ):
        removed = await remove_file_from_references(
            str(uuid.uuid4()), str(uuid.uuid4()), revision=1
        )

    assert removed == []
    _stub_persist_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_returns_empty_when_no_match_for_file_id(_stub_persist_state):
    other_file_id = str(uuid.uuid4())
    state = _make_state(
        [
            ReferenceFileMatch(
                reference_id="r1",
                file_id=other_file_id,
                source=MatchSource.AUTO_MATCHED,
            )
        ]
    )

    with patch(
        "lib.services.references._get_file_matching_workflow_state",
        new=AsyncMock(return_value=(_make_run(), state)),
    ):
        removed = await remove_file_from_references(
            str(uuid.uuid4()), str(uuid.uuid4()), revision=1
        )

    assert removed == []
    _stub_persist_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_removes_single_match_and_preserves_others(_stub_persist_state):
    target_file_id = str(uuid.uuid4())
    other_file_id = str(uuid.uuid4())
    keep = ReferenceFileMatch(
        reference_id="r_keep", file_id=other_file_id, source=MatchSource.AUTO_MATCHED
    )
    drop = ReferenceFileMatch(
        reference_id="r_drop", file_id=target_file_id, source=MatchSource.AUTO_MATCHED
    )
    state = _make_state([keep, drop])
    run = _make_run()

    with patch(
        "lib.services.references._get_file_matching_workflow_state",
        new=AsyncMock(return_value=(run, state)),
    ):
        removed = await remove_file_from_references(
            str(uuid.uuid4()), target_file_id, revision=1
        )

    assert removed == ["r_drop"]
    _stub_persist_state.assert_awaited_once()
    run_id_arg, persisted_state = _stub_persist_state.await_args.args
    assert run_id_arg == str(run.id)
    assert persisted_state.matches == [keep]


@pytest.mark.asyncio
async def test_removes_multiple_matches_pointing_at_same_file(_stub_persist_state):
    target_file_id = str(uuid.uuid4())
    dup_a = ReferenceFileMatch(
        reference_id="ra", file_id=target_file_id, source=MatchSource.AUTO_MATCHED
    )
    dup_b = ReferenceFileMatch(
        reference_id="rb", file_id=target_file_id, source=MatchSource.AUTO_FETCHED
    )
    state = _make_state([dup_a, dup_b])

    with patch(
        "lib.services.references._get_file_matching_workflow_state",
        new=AsyncMock(return_value=(_make_run(), state)),
    ):
        removed = await remove_file_from_references(
            str(uuid.uuid4()), target_file_id, revision=1
        )

    assert sorted(removed) == ["ra", "rb"]
    persisted_state = _stub_persist_state.await_args.args[1]
    assert persisted_state.matches == []
