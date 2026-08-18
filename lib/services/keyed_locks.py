"""A registry that hands out one ``asyncio.Lock`` per key.

Serialising work per project / per workflow run needs a lock that every caller
for the same key can find. Keeping those locks in an ``lru_cache`` bounds memory
but breaks the guarantee they exist for: an LRU evicts by recency, not by
whether a lock is currently held, so unrelated keys can push a *held* lock out
of the cache and the next caller for that key is handed a brand-new lock and
walks straight into the critical section.

Holding the locks weakly bounds memory the other way round: an entry lives
exactly as long as somebody is using it (the caller's own reference, plus every
waiter blocked on it, keeps it alive) and disappears once nobody is.

Callers must therefore keep the lock in a local variable for as long as they
need it — ``lock = registry.get(key)`` then ``async with lock:`` — which is what
``async with registry.get(key):`` does anyway.
"""

import asyncio
import threading
import weakref
from typing import Generic, Hashable, TypeVar

KeyT = TypeVar("KeyT", bound=Hashable)


class KeyedLockRegistry(Generic[KeyT]):
    """Process-wide registry of per-key ``asyncio.Lock`` objects."""

    def __init__(self) -> None:
        self._locks: weakref.WeakValueDictionary[KeyT, asyncio.Lock] = (
            weakref.WeakValueDictionary()
        )
        # Guards the get-or-create so two callers arriving at the same time
        # cannot each install a different lock for the same key. The body never
        # awaits, so this is only ever held for a few instructions.
        self._guard = threading.Lock()

    def get(self, key: KeyT) -> asyncio.Lock:
        """Return the lock for ``key``, creating it if nobody holds one."""
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock

    def __len__(self) -> int:
        """Number of locks currently in use (live entries only)."""
        return len(self._locks)
