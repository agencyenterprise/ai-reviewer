"""Integration tests for get_workflow_duration_estimates.

The function aggregates the whole workflow_runs table, which other tests write
to in parallel. To get exact numbers, each test runs inside one REPEATABLE READ
transaction that is rolled back at the end: the service reads through that same
transaction, so it sees a fixed snapshot plus this test's uncommitted rows, and
nobody else ever sees them. Tests then only assert on workflow types that had
no completed runs in the snapshot.
"""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from lib.config.database import async_engine
from lib.models.workflow_run import WorkflowRun, WorkflowRunStatus
from lib.services import workflow_duration_estimates
from lib.services.workflow_duration_estimates import (
    WorkflowDurationEstimate,
    get_workflow_duration_estimates,
)
from lib.workflows.models import WorkflowRunType

START = datetime(2026, 1, 1, tzinfo=UTC)


@pytest_asyncio.fixture
async def session(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncSession]:
    """A session in a snapshot transaction that the service also reads through."""
    async with async_engine.connect() as conn:
        await conn.execution_options(isolation_level="REPEATABLE READ")
        await conn.begin()
        snapshot = AsyncSession(bind=conn, expire_on_commit=False)

        @asynccontextmanager
        async def _same_session() -> AsyncIterator[AsyncSession]:
            yield snapshot

        monkeypatch.setattr(
            workflow_duration_estimates, "get_async_db_session", _same_session
        )
        try:
            yield snapshot
        finally:
            await snapshot.close()
            await conn.rollback()


@pytest_asyncio.fixture
async def free_types(session: AsyncSession) -> list[WorkflowRunType]:
    """Workflow types with no completed runs in this test's snapshot."""
    taken = {e.type for e in (await get_workflow_duration_estimates()).estimates}
    return [t for t in WorkflowRunType if t not in taken]


def _run(
    workflow_type: str,
    seconds: float | None,
    status: WorkflowRunStatus = WorkflowRunStatus.COMPLETED,
    started: bool = True,
) -> WorkflowRun:
    return WorkflowRun(
        id=uuid.uuid4(),
        project_id=None,
        type=workflow_type,  # type: ignore[arg-type]  # raw string covers retired types
        langgraph_thread_id=str(uuid.uuid4()),
        status=status,
        started_at=START if started else None,
        completed_at=None if seconds is None else START + timedelta(seconds=seconds),
    )


async def _estimates_for(
    session: AsyncSession, runs: list[WorkflowRun]
) -> dict[str, WorkflowDurationEstimate]:
    session.add_all(runs)
    await session.flush()
    response = await get_workflow_duration_estimates()
    return {e.type.value: e for e in response.estimates}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "durations, median",
    [
        ([10, 20, 90], 20.0),  # odd count: the middle run, not the 40s mean
        ([10, 20], 15.0),  # even count: percentile_cont interpolates
        ([7.5], 7.5),
    ],
)
async def test_estimate_is_the_median_completed_duration(
    session, free_types, durations, median
):
    workflow_type = free_types[0]

    estimates = await _estimates_for(
        session, [_run(workflow_type, seconds) for seconds in durations]
    )

    estimate = estimates[workflow_type.value]
    assert estimate.estimated_seconds == pytest.approx(median)
    assert estimate.sample_size == len(durations)


@pytest.mark.asyncio
async def test_only_completed_runs_with_both_timestamps_count(session, free_types):
    workflow_type = free_types[0]
    ignored = [
        _run(workflow_type, 1000, status=WorkflowRunStatus.FAILED),
        _run(workflow_type, 1000, status=WorkflowRunStatus.CANCELLED),
        _run(workflow_type, 1000, started=False),
        _run(workflow_type, None),
    ]

    estimates = await _estimates_for(session, [_run(workflow_type, 30), *ignored])

    assert estimates[workflow_type.value].estimated_seconds == pytest.approx(30)
    assert estimates[workflow_type.value].sample_size == 1


@pytest.mark.asyncio
async def test_types_without_completed_runs_are_left_out(session, free_types):
    workflow_type = free_types[0]

    estimates = await _estimates_for(
        session, [_run(workflow_type, 30, status=WorkflowRunStatus.FAILED)]
    )

    assert workflow_type.value not in estimates


@pytest.mark.asyncio
async def test_retired_workflow_types_are_skipped(session):
    retired = f"retired_{uuid.uuid4().hex}"

    estimates = await _estimates_for(session, [_run(retired, 30)])

    assert retired not in estimates
