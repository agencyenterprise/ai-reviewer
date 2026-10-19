"""Tests for the shared per-item state helpers in lib/workflows/reducers.py."""

from enum import Enum

import pytest
from langgraph.graph import StateGraph
from pydantic import BaseModel

from lib.workflows.abbreviation_scan_v2.chunk_models import (
    AbbreviationChunk,
    ChunkStatus,
)
from lib.workflows.abbreviation_scan_v2.manifest import AbbreviationScanV2Manifest
from lib.workflows.abbreviation_scan_v2.state import AbbreviationScanV2State
from lib.workflows.claim_reference_validation_v2.manifest import (
    ClaimReferenceValidationV2Manifest,
)
from lib.workflows.claim_reference_validation_v2.state import (
    ClaimReferenceValidationV2State,
    SectionVerificationItem,
    SectionVerificationStatus,
)
from lib.workflows.document_summarization.state import (
    DocumentSummarizationState,
    FileSummary,
)
from lib.workflows.reducers import cancel_pending, upsert_by
from lib.workflows.reference_downloader.manifest import ReferenceDownloaderManifest
from lib.workflows.reference_downloader.state import (
    ReferenceDownloaderState,
    ReferenceFetchResult,
    ReferenceFetchStatus,
)
from lib.workflows.reference_validation_v2.manifest import ReferenceValidationV2Manifest
from lib.workflows.reference_validation_v2.state import (
    ReferenceValidationV2Item,
    ReferenceValidationV2State,
    ReferenceValidationV2Status,
)
from lib.workflows.state_updates import apply_node_update


class Status(str, Enum):
    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


class Item(BaseModel):
    id: int
    status: Status = Status.PENDING
    label: str = ""


def _ids(items: list[Item]) -> list[int]:
    return [item.id for item in items]


# --- upsert_by ---


def test_upsert_replaces_matching_keys_in_place():
    merge = upsert_by(lambda item: item.id)
    existing = [Item(id=3), Item(id=1), Item(id=2)]
    done = Item(id=1, status=Status.DONE)

    merged = merge(existing, [done])

    assert _ids(merged) == [3, 1, 2]
    assert merged[1] is done
    assert merged[0] is existing[0] and merged[2] is existing[2]


def test_upsert_appends_new_keys_in_arrival_order():
    merge = upsert_by(lambda item: item.id)

    merged = merge([Item(id=5)], [Item(id=9), Item(id=7)])

    assert _ids(merged) == [5, 9, 7]


def test_upsert_last_update_wins_for_a_repeated_key():
    merge = upsert_by(lambda item: item.id)

    merged = merge([Item(id=1)], [Item(id=1, label="a"), Item(id=1, label="b")])

    assert [(item.id, item.label) for item in merged] == [(1, "b")]


def test_upsert_with_sort_orders_by_key():
    merge = upsert_by(lambda item: item.id, sort=True)

    merged = merge([Item(id=3), Item(id=1)], [Item(id=2), Item(id=0)])

    assert _ids(merged) == [0, 1, 2, 3]


def test_upsert_handles_empty_sides_and_leaves_inputs_alone():
    merge = upsert_by(lambda item: item.id)
    existing = [Item(id=1)]
    new = [Item(id=2)]

    assert merge([], []) == []
    assert _ids(merge(existing, [])) == [1]
    assert _ids(merge([], new)) == [2]
    merge(existing, new)
    assert _ids(existing) == [1] and _ids(new) == [2]


# --- cancel_pending ---


def test_cancel_pending_marks_only_pending_items():
    items = [
        Item(id=1, status=Status.DONE),
        Item(id=2),
        Item(id=3, status=Status.CANCELLED),
        Item(id=4),
    ]

    cancelled = cancel_pending(items, Status.PENDING, Status.CANCELLED)

    assert [item.status for item in cancelled] == [
        Status.DONE,
        Status.CANCELLED,
        Status.CANCELLED,
        Status.CANCELLED,
    ]
    assert cancelled[0] is items[0] and cancelled[2] is items[2]
    assert items[1].status == Status.PENDING  # copies, never mutates


def test_cancel_pending_empty():
    assert cancel_pending([], Status.PENDING, Status.CANCELLED) == []


# --- wiring: each workflow's state field merges through LangGraph by its key ---


def _summary(file_id: str, title: str) -> FileSummary:
    return FileSummary(
        file_id=file_id,
        title=title,
        authors="",
        publication_date="",
        abstract="",
        summary="",
    )


WIRING = [
    pytest.param(
        ReferenceDownloaderState,
        "fetched_references",
        [
            ReferenceFetchResult(reference_id="b", input_reference="B"),
            ReferenceFetchResult(reference_id="a", input_reference="A"),
        ],
        ReferenceFetchResult(
            reference_id="a", input_reference="A", status=ReferenceFetchStatus.COMPLETED
        ),
        ReferenceFetchResult(reference_id="c", input_reference="C"),
        ["b", "a", "c"],
        lambda item: item.reference_id,
        id="reference_downloader",
    ),
    pytest.param(
        ReferenceValidationV2State,
        "reference_validations",
        [
            ReferenceValidationV2Item(reference_id="b", input_reference="B"),
            ReferenceValidationV2Item(reference_id="a", input_reference="A"),
        ],
        ReferenceValidationV2Item(
            reference_id="a",
            input_reference="A",
            status=ReferenceValidationV2Status.COMPLETED,
        ),
        ReferenceValidationV2Item(reference_id="c", input_reference="C"),
        ["b", "a", "c"],
        lambda item: item.reference_id,
        id="reference_validation_v2",
    ),
    pytest.param(
        ClaimReferenceValidationV2State,
        "section_verifications",
        [
            SectionVerificationItem(section_index=2),
            SectionVerificationItem(section_index=0),
        ],
        SectionVerificationItem(
            section_index=0, status=SectionVerificationStatus.COMPLETED
        ),
        SectionVerificationItem(section_index=1),
        [2, 0, 1],
        lambda item: item.section_index,
        id="claim_reference_validation_v2",
    ),
    pytest.param(
        DocumentSummarizationState,
        "summaries",
        [_summary("f2", "old"), _summary("f1", "old")],
        _summary("f1", "new"),
        _summary("f3", "new"),
        ["f2", "f1", "f3"],
        lambda item: item.file_id,
        id="document_summarization",
    ),
    pytest.param(
        AbbreviationScanV2State,
        "chunks",
        [
            AbbreviationChunk(chunk_index=2, start_line=3, end_line=3),
            AbbreviationChunk(chunk_index=0, start_line=1, end_line=1),
        ],
        AbbreviationChunk(
            chunk_index=0, start_line=1, end_line=1, status=ChunkStatus.COMPLETED
        ),
        AbbreviationChunk(chunk_index=1, start_line=2, end_line=2),
        [0, 1, 2],  # chunks are kept in chunk order
        lambda item: item.chunk_index,
        id="abbreviation_scan_v2",
    ),
]


@pytest.mark.parametrize(
    ("state_type", "field", "existing", "replacement", "added", "expected", "key"),
    WIRING,
)
def test_state_field_upserts_by_its_key(
    state_type, field, existing, replacement, added, expected, key
):
    state = state_type.model_construct(**{field: existing})
    channels = StateGraph(state_type).channels

    merged = getattr(
        apply_node_update(state, {field: [replacement, added]}, channels), field
    )

    assert [key(item) for item in merged] == expected
    assert any(item is replacement for item in merged)
    assert len(merged) == len(existing) + 1


# --- wiring: each manifest's on_cancel cancels its pending items ---

CANCEL_WIRING = [
    pytest.param(
        ReferenceDownloaderManifest,
        ReferenceDownloaderState,
        "fetched_references",
        [
            ReferenceFetchResult(
                reference_id="a",
                input_reference="A",
                status=ReferenceFetchStatus.COMPLETED,
            ),
            ReferenceFetchResult(reference_id="b", input_reference="B"),
        ],
        [ReferenceFetchStatus.COMPLETED, ReferenceFetchStatus.CANCELLED],
        id="reference_downloader",
    ),
    pytest.param(
        ReferenceValidationV2Manifest,
        ReferenceValidationV2State,
        "reference_validations",
        [
            ReferenceValidationV2Item(
                reference_id="a",
                input_reference="A",
                status=ReferenceValidationV2Status.ERROR,
            ),
            ReferenceValidationV2Item(reference_id="b", input_reference="B"),
        ],
        [ReferenceValidationV2Status.ERROR, ReferenceValidationV2Status.CANCELLED],
        id="reference_validation_v2",
    ),
    pytest.param(
        ClaimReferenceValidationV2Manifest,
        ClaimReferenceValidationV2State,
        "section_verifications",
        [
            SectionVerificationItem(
                section_index=0, status=SectionVerificationStatus.PARTIAL
            ),
            SectionVerificationItem(section_index=1),
        ],
        [SectionVerificationStatus.PARTIAL, SectionVerificationStatus.CANCELLED],
        id="claim_reference_validation_v2",
    ),
    pytest.param(
        AbbreviationScanV2Manifest,
        AbbreviationScanV2State,
        "chunks",
        [
            AbbreviationChunk(
                chunk_index=0, start_line=1, end_line=1, status=ChunkStatus.SKIPPED
            ),
            AbbreviationChunk(chunk_index=1, start_line=2, end_line=2),
        ],
        [ChunkStatus.SKIPPED, ChunkStatus.CANCELLED],
        id="abbreviation_scan_v2",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("manifest_type", "state_type", "field", "items", "expected"), CANCEL_WIRING
)
async def test_on_cancel_cancels_pending_items(
    manifest_type, state_type, field, items, expected
):
    state = state_type.model_construct(**{field: items})

    cancelled = await manifest_type().on_cancel(state)

    assert [item.status for item in getattr(cancelled, field)] == expected
