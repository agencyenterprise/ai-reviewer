"""The admin dashboard endpoint's cache is what keeps repeat loads off the DB.

Each computation is a set of sequential scans over `workflow_runs` holding one
pooled connection, so "several admins refresh at once" must not mean "several
sets of scans". These tests pin the two properties that guarantee it: concurrent
callers share one in-flight computation, and each window is cached separately.
"""

import asyncio

import aiotools
import pytest

from lib.api.routers import admin_dashboard


@pytest.fixture(autouse=True)
def clear_cache():
    admin_dashboard._cached_dashboard.cache_clear()
    yield
    admin_dashboard._cached_dashboard.cache_clear()


class _Recorder:
    """Stands in for the service, counting how often it is actually run."""

    def __init__(self) -> None:
        self.calls: list[int] = []

    async def __call__(self, days: int) -> str:
        self.calls.append(days)
        await asyncio.sleep(0.05)  # long enough for the other callers to arrive
        return f"payload-{days}"


@pytest.mark.asyncio
async def test_concurrent_requests_for_one_window_share_a_single_computation(
    monkeypatch,
):
    recorder = _Recorder()
    monkeypatch.setattr(admin_dashboard, "get_admin_dashboard", recorder)

    results = await asyncio.gather(
        *[admin_dashboard._cached_dashboard(30) for _ in range(25)]
    )

    assert recorder.calls == [30]
    assert results == ["payload-30"] * 25


@pytest.mark.asyncio
async def test_a_second_load_of_the_same_window_is_served_from_the_cache(monkeypatch):
    recorder = _Recorder()
    monkeypatch.setattr(admin_dashboard, "get_admin_dashboard", recorder)

    first = await admin_dashboard._cached_dashboard(7)
    second = await admin_dashboard._cached_dashboard(7)

    assert recorder.calls == [7]
    assert first == second


@pytest.mark.asyncio
async def test_each_window_is_cached_separately(monkeypatch):
    recorder = _Recorder()
    monkeypatch.setattr(admin_dashboard, "get_admin_dashboard", recorder)

    for days in (7, 30, 90, 365):
        await admin_dashboard._cached_dashboard(days)

    assert recorder.calls == [7, 30, 90, 365]


def test_cache_is_bounded():
    """A caller churning `days` values must not grow the cache without bound."""
    assert admin_dashboard._cached_dashboard.cache_parameters()["maxsize"] == (
        admin_dashboard._CACHE_MAXSIZE
    )


@pytest.mark.asyncio
async def test_entries_are_recomputed_once_the_ttl_passes():
    """The property `CACHE_TTL_SECONDS` relies on, at a testable timescale.

    `cache_parameters()` does not report the TTL, so the expiry semantics the
    endpoint depends on are pinned here against the same decorator instead.
    """
    calls: list[int] = []

    @aiotools.lru_cache(maxsize=admin_dashboard._CACHE_MAXSIZE, expire_after=0.1)
    async def cached(days: int) -> int:
        calls.append(days)
        return days

    await cached(30)
    await cached(30)
    assert calls == [30]

    await asyncio.sleep(0.15)
    await cached(30)

    assert calls == [30, 30]
