"""Unit tests for the per-key asyncio lock registry."""

import asyncio
import gc

import pytest

from lib.services.keyed_locks import KeyedLockRegistry


class TestKeyedLockRegistry:
    """Tests for KeyedLockRegistry."""

    def test_same_key_returns_the_same_lock(self):
        registry: KeyedLockRegistry[str] = KeyedLockRegistry()

        lock = registry.get("project-1")
        assert registry.get("project-1") is lock

    def test_different_keys_get_different_locks(self):
        registry: KeyedLockRegistry[str] = KeyedLockRegistry()

        assert registry.get("project-1") is not registry.get("project-2")

    def test_tuple_keys_are_supported(self):
        registry: KeyedLockRegistry[tuple[str, int]] = KeyedLockRegistry()

        lock = registry.get(("run", 1))
        assert registry.get(("run", 1)) is lock
        assert registry.get(("run", 2)) is not lock

    def test_held_lock_survives_unrelated_traffic(self):
        """Other keys must never displace a lock its holder is still using."""
        registry: KeyedLockRegistry[str] = KeyedLockRegistry()

        lock = registry.get("busy-project")
        for i in range(1000):
            registry.get(f"other-project-{i}")

        assert registry.get("busy-project") is lock

    def test_unused_locks_are_dropped(self):
        """Memory stays bounded: entries go away once nobody references them."""
        registry: KeyedLockRegistry[str] = KeyedLockRegistry()

        for i in range(100):
            registry.get(f"project-{i}")
        gc.collect()

        assert len(registry) == 0

    def test_lock_in_use_is_kept(self):
        registry: KeyedLockRegistry[str] = KeyedLockRegistry()

        held = registry.get("project-1")
        for i in range(100):
            registry.get(f"project-other-{i}")
        gc.collect()

        assert len(registry) == 1
        assert registry.get("project-1") is held

    @pytest.mark.asyncio
    async def test_serializes_callers_sharing_a_key(self):
        registry: KeyedLockRegistry[str] = KeyedLockRegistry()
        concurrent = 0
        max_concurrent = 0

        async def critical_section() -> None:
            nonlocal concurrent, max_concurrent
            lock = registry.get("project-1")
            async with lock:
                concurrent += 1
                max_concurrent = max(max_concurrent, concurrent)
                await asyncio.sleep(0)
                concurrent -= 1

        await asyncio.gather(*(critical_section() for _ in range(5)))

        assert max_concurrent == 1

    @pytest.mark.asyncio
    async def test_serializes_even_while_other_keys_are_busy(self):
        """The regression: churn on other keys must not unlock a held key."""
        registry: KeyedLockRegistry[str] = KeyedLockRegistry()
        concurrent = 0
        max_concurrent = 0

        async def critical_section(worker: int) -> None:
            nonlocal concurrent, max_concurrent
            lock = registry.get("project-1")
            async with lock:
                concurrent += 1
                max_concurrent = max(max_concurrent, concurrent)
                # Traffic from other projects arriving mid-update.
                for i in range(500):
                    registry.get(f"other-project-{worker}-{i}")
                await asyncio.sleep(0)
                concurrent -= 1

        await asyncio.gather(critical_section(1), critical_section(2))

        assert max_concurrent == 1

    @pytest.mark.asyncio
    async def test_different_keys_run_in_parallel(self):
        """Serialisation is per key: unrelated keys must not block each other."""
        registry: KeyedLockRegistry[str] = KeyedLockRegistry()
        started = asyncio.Event()
        release = asyncio.Event()

        async def first() -> None:
            lock = registry.get("project-1")
            async with lock:
                started.set()
                await release.wait()

        async def second() -> None:
            await started.wait()
            lock = registry.get("project-2")
            async with lock:
                release.set()

        await asyncio.wait_for(asyncio.gather(first(), second()), timeout=1)
