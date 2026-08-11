"""Tests for the shared checkpointer pool.

Two invariants, both easy to break by writing the obvious thing instead: one pool shared
by every saver, and a fresh saver per call so each run gets its own lock. They fail
silently -- as connection exhaustion, or as unexplained latency -- so they are asserted.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.agents import checkpointer as checkpointer_module
from lib.agents.checkpointer import (
    checkpointer_pool,
    close_checkpointer_pool,
    get_checkpointer,
)

# Captured before the autouse fixture below replaces it, so the tests that are *about*
# setup exercise the real thing rather than their own stub.
run_setup = checkpointer_module._run_setup


@pytest.fixture(autouse=True)
def reset_pool_state() -> Any:
    """Reset the module's opened flag and stub everything that touches Postgres."""

    checkpointer_module._opened = False
    with (
        patch.object(checkpointer_pool, "open", new_callable=AsyncMock) as mock_open,
        patch.object(checkpointer_pool, "close", new_callable=AsyncMock) as mock_close,
        patch.object(
            checkpointer_module, "_run_setup", new_callable=AsyncMock
        ) as mock_setup,
    ):
        yield mock_open, mock_close, mock_setup
    checkpointer_module._opened = False


class TestTheSharedPool:
    @pytest.mark.asyncio
    async def test_savers_share_the_pool(self) -> None:
        async with get_checkpointer() as saver_a:
            async with get_checkpointer() as saver_b:
                assert saver_a.conn is checkpointer_pool
                assert saver_b.conn is checkpointer_pool

    @pytest.mark.asyncio
    async def test_savers_are_distinct_so_runs_do_not_queue(self) -> None:
        """Each saver's lock is its own, or one thread's write blocks every other."""

        async with get_checkpointer() as saver_a:
            async with get_checkpointer() as saver_b:
                assert saver_a is not saver_b
                assert saver_a.lock is not saver_b.lock

    @pytest.mark.asyncio
    async def test_the_pool_is_opened_and_verified_once(
        self, reset_pool_state: Any
    ) -> None:
        mock_open, _, mock_setup = reset_pool_state

        for _ in range(3):
            async with get_checkpointer():
                pass

        assert mock_open.await_count == 1
        assert mock_setup.await_count == 1

    @pytest.mark.asyncio
    async def test_simultaneous_first_use_still_opens_once(
        self, reset_pool_state: Any
    ) -> None:
        """The double-checked lock, under the case it exists for.

        Every worker's first checkpointed run can arrive at once after a deploy.
        """

        mock_open, _, mock_setup = reset_pool_state

        async def use() -> Any:
            async with get_checkpointer() as saver:
                return saver

        savers = await asyncio.gather(*[use() for _ in range(20)])

        assert len(savers) == 20
        assert all(saver.conn is checkpointer_pool for saver in savers)
        assert mock_open.await_count == 1
        assert mock_setup.await_count == 1


class TestShutdown:
    @pytest.mark.asyncio
    async def test_closing_lets_a_later_call_reopen(
        self, reset_pool_state: Any
    ) -> None:
        """A reload closes the pool; the next run must still work."""

        mock_open, mock_close, mock_setup = reset_pool_state

        async with get_checkpointer():
            pass
        await close_checkpointer_pool()
        async with get_checkpointer():
            pass

        assert mock_close.await_count == 1
        assert mock_open.await_count == 2
        assert mock_setup.await_count == 2

    @pytest.mark.asyncio
    async def test_closing_what_was_never_opened_does_nothing(
        self, reset_pool_state: Any
    ) -> None:
        """A process may never open the pool, and shutdown still runs there."""

        _, mock_close, _ = reset_pool_state

        await close_checkpointer_pool()

        assert mock_close.await_count == 0


class TestSetupAcrossWorkers:
    """``setup()`` is a migration runner, and four workers race it on a fresh database.

    ``checkpoint_migrations.v`` is a primary key, so two workers reading the same
    version both try to insert it and one dies on a duplicate key. The advisory lock is
    what makes that impossible, and it has to be released by hand: the pool runs in
    autocommit, so nothing else ever will.
    """

    @pytest.mark.asyncio
    async def test_setup_runs_under_an_advisory_lock_and_releases_it(self) -> None:
        connection = MagicMock()
        connection.execute = AsyncMock()
        pool_connection = MagicMock()
        pool_connection.__aenter__ = AsyncMock(return_value=connection)
        pool_connection.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(
                checkpointer_pool, "connection", MagicMock(return_value=pool_connection)
            ),
            patch.object(
                checkpointer_module.AsyncPostgresSaver,
                "setup",
                new_callable=AsyncMock,
            ) as setup,
        ):
            await run_setup()

        statements = [call.args[0] for call in connection.execute.await_args_list]
        keys = [call.args[1] for call in connection.execute.await_args_list]

        assert "pg_advisory_lock" in statements[0]
        assert "pg_advisory_unlock" in statements[-1]
        assert setup.await_count == 1
        assert keys[0] == keys[-1] == (checkpointer_module.SETUP_LOCK_KEY,)

    @pytest.mark.asyncio
    async def test_the_lock_is_released_even_when_setup_fails(self) -> None:
        """Otherwise a failed deploy leaves every other worker waiting on it."""

        connection = MagicMock()
        connection.execute = AsyncMock()
        pool_connection = MagicMock()
        pool_connection.__aenter__ = AsyncMock(return_value=connection)
        pool_connection.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(
                checkpointer_pool, "connection", MagicMock(return_value=pool_connection)
            ),
            patch.object(
                checkpointer_module.AsyncPostgresSaver,
                "setup",
                new_callable=AsyncMock,
                side_effect=RuntimeError("migration failed"),
            ),
            pytest.raises(RuntimeError, match="migration failed"),
        ):
            await run_setup()

        statements = [call.args[0] for call in connection.execute.await_args_list]
        assert "pg_advisory_unlock" in statements[-1]
