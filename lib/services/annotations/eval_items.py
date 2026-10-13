"""Annotation items built from an issue-inventory eval dataset.

Every anchored expected issue and every decoy becomes an item the set's spec
answers (by default "should be flagged" and "should be left alone"), so
annotators judge the same passages the eval scores. The dataset is read with
the evals' own loader, so anchors resolve exactly as they do for the scorers.
"""

import hashlib
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from evals_inspectai.common.issue_inventory import (
    ResolvedInventory,
    load_inventory_records,
    normalize,
)
from evals_inspectai.common.loaders import inline_local_images
from lib.models.annotation import AnnotationItemKind
from lib.services.annotations.set_spec import AnnotationSetSpec, ItemReference
from lib.services.annotations.models import AnnotationPassage


class AnnotationItemDraft(BaseModel):
    """An item as the dataset defines it, before it is written to the database."""

    source_key: str
    kind: AnnotationItemKind
    passage: AnnotationPassage
    reference_answers: dict[str, str]
    reference_explanation: Optional[str]


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _source_key(document: str, anchor: str, kind: AnnotationItemKind) -> str:
    """Content-addressed: editing the document, one of its figures or the passage
    makes a new item, so no answer carries over to evidence it was not given on."""
    return f"{_digest(document)}:{_digest(normalize(anchor))}:{kind.value}"


def _line_of(document: str, anchor: str) -> Optional[int]:
    target = normalize(anchor)
    for number, line in enumerate(document.split("\n"), 1):
        if target in normalize(line):
            return number
    return None


def _item(
    document: str,
    anchor: str,
    kind: AnnotationItemKind,
    reference: Optional[ItemReference],
    line: Optional[int] = None,
) -> Optional[AnnotationItemDraft]:
    if reference is None:
        return None
    return AnnotationItemDraft(
        source_key=_source_key(document, anchor, kind),
        kind=kind,
        passage=AnnotationPassage(
            document=document, anchor=anchor, line=line or _line_of(document, anchor)
        ),
        reference_answers=reference.answers,
        reference_explanation=reference.explanation,
    )


def _record_items(
    record: ResolvedInventory, spec: AnnotationSetSpec
) -> list[Optional[AnnotationItemDraft]]:
    # Figures are inlined so the annotation screen shows them as the run sees them;
    # each stays on its own line, so line numbers are unchanged.
    document = inline_local_images(record.document)
    # An issue about something absent has no passage to show.
    candidates = [
        _item(
            document,
            issue.anchor,
            AnnotationItemKind.EXPECTED_ISSUE,
            spec.issue_reference(issue),
            issue.line,
        )
        for issue in record.expected_issues
        if issue.anchor is not None
    ]
    candidates += [
        _item(
            document,
            decoy.anchor,
            AnnotationItemKind.DECOY,
            spec.decoy_reference(decoy),
        )
        for decoy in record.decoys
    ]
    return candidates


def items_from_inventory(
    spec: AnnotationSetSpec, path: Optional[Path] = None
) -> list[AnnotationItemDraft]:
    """One item per anchored passage in the dataset, deduplicated by source key."""
    drafts: dict[str, AnnotationItemDraft] = {}
    for record in load_inventory_records(path or spec.dataset_path):
        for draft in _record_items(record, spec):
            if draft is not None:
                drafts.setdefault(draft.source_key, draft)
    return list(drafts.values())
