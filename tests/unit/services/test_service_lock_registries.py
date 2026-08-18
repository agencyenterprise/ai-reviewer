"""The service-level lock registries must stay exclusive under key churn.

Both registries hand out one lock per key while a critical section reads,
modifies and writes shared state. Traffic on unrelated keys — other projects,
other workflow runs — must never let a second caller into the same key's
critical section.
"""

import asyncio
import uuid

import pytest

from lib.services.references import _get_project_lock, _project_lock
from lib.services.workflow_progress import _get_progress_lock


class TestProjectLock:
    """Tests for the per-project lock used by the reference services."""

    @pytest.mark.asyncio
    async def test_serializes_while_other_projects_are_busy(self):
        concurrent = 0
        max_concurrent = 0

        async def update_reference_state(worker: int) -> None:
            nonlocal concurrent, max_concurrent
            async with _project_lock("project-under-test"):
                concurrent += 1
                max_concurrent = max(max_concurrent, concurrent)
                for i in range(500):
                    _get_project_lock(f"other-project-{worker}-{i}")
                await asyncio.sleep(0)
                concurrent -= 1

        await asyncio.gather(update_reference_state(1), update_reference_state(2))

        assert max_concurrent == 1

    @pytest.mark.asyncio
    async def test_does_not_block_other_projects(self):
        started = asyncio.Event()
        release = asyncio.Event()

        async def holder() -> None:
            async with _project_lock("project-a"):
                started.set()
                await release.wait()

        async def other() -> None:
            await started.wait()
            async with _project_lock("project-b"):
                release.set()

        await asyncio.wait_for(asyncio.gather(holder(), other()), timeout=1)


class TestProgressLock:
    """Tests for the per-(workflow run, node name) progress lock."""

    @pytest.mark.asyncio
    async def test_serializes_while_other_runs_are_busy(self):
        concurrent = 0
        max_concurrent = 0
        workflow_run_id = uuid.uuid4()
        name = "Extract references"

        async def get_or_create(worker: int) -> None:
            nonlocal concurrent, max_concurrent
            lock = _get_progress_lock(workflow_run_id, name)
            async with lock:
                concurrent += 1
                max_concurrent = max(max_concurrent, concurrent)
                for i in range(500):
                    _get_progress_lock(uuid.uuid4(), f"node-{worker}-{i}")
                await asyncio.sleep(0)
                concurrent -= 1

        await asyncio.gather(get_or_create(1), get_or_create(2))

        assert max_concurrent == 1

    def test_is_scoped_to_run_and_name(self):
        workflow_run_id = uuid.uuid4()
        lock = _get_progress_lock(workflow_run_id, "node-a")

        assert _get_progress_lock(workflow_run_id, "node-a") is lock
        assert _get_progress_lock(workflow_run_id, "node-b") is not lock
        assert _get_progress_lock(uuid.uuid4(), "node-a") is not lock
