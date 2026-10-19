"""Shared helpers for per-item workflow state: fan-out reducers and cancel cleanup."""

from collections.abc import Callable, Mapping
from enum import Enum
from typing import Any, Protocol, Self, TypeVar

KeyT = TypeVar("KeyT", int, str)
ItemT = TypeVar("ItemT")


class _StatusItem(Protocol):
    status: Any

    def model_copy(
        self, *, update: Mapping[str, Any] | None = None, deep: bool = False
    ) -> Self: ...


StatusItemT = TypeVar("StatusItemT", bound=_StatusItem)

# A LangGraph reducer for a list field: (existing, update) -> merged.
Reducer = Callable[[list[ItemT], list[ItemT]], list[ItemT]]


def upsert_by(key: Callable[[ItemT], KeyT], *, sort: bool = False) -> Reducer[ItemT]:
    """Build a LangGraph reducer that merges items by ``key``.

    Each new item replaces the existing one with the same key (so a fan-out
    result replaces its PENDING row); items with new keys are appended. The
    result keeps first-insertion order, or is sorted by key when ``sort`` is set.
    """

    def merge(existing: list[ItemT], new: list[ItemT]) -> list[ItemT]:
        by_key = {key(item): item for item in existing}
        for item in new:
            by_key[key(item)] = item
        if sort:
            return [by_key[k] for k in sorted(by_key)]
        return list(by_key.values())

    return merge


def cancel_pending(
    items: list[StatusItemT], pending: Enum, cancelled: Enum
) -> list[StatusItemT]:
    """Return ``items`` with every ``pending`` item marked ``cancelled``.

    Used by manifests' ``on_cancel`` so the items a cancelled run never reached
    don't show as in progress.
    """
    return [
        item.model_copy(update={"status": cancelled})
        if item.status == pending
        else item
        for item in items
    ]
