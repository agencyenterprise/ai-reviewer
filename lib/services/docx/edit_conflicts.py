"""Deciding which proposed edits may be applied to the document at once.

Two workflows can propose edits that touch the same words: a reference checker
rewriting a citation inside a sentence an advocacy-tone check wants reworded.
Applying both would corrupt the passage -- and the redline library silently
corrupts a paragraph when one operation's search text overlaps text an earlier
operation inserted -- so overlapping edits have to be reduced to one winner
before anything is written.

The rules are pure and deterministic: given the same edits and the same
document, the same edit wins, whatever order the rows arrive in.
"""

import uuid
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel

from lib.models.issue_edit import IssueEdit, IssueEditStatus
from lib.services.text_location import locate_in_paragraph
from lib.workflows.models import SeverityEnum
from lib.workflows.simple_deep_agent.edit_anchoring import normalize_whitespace

EditOutcomeName = Literal["apply", "conflict", "unlocatable", "rejected"]


class EditCandidate(BaseModel):
    """One proposed edit, with the issue metadata the tie-breaks need."""

    edit: IssueEdit
    issue_severity: SeverityEnum
    issue_created_at: datetime
    workflow_type: str


class EditDecision(BaseModel):
    """What is to be done with one candidate edit.

    ``span`` is the ``[start, end)`` offset pair of the quote inside its
    markdown line, present whenever the quote could be located. A ``conflict``
    decision names the edit that beat it in ``winner_id``.
    """

    edit_id: uuid.UUID
    line: int
    span: tuple[int, int] | None
    outcome: EditOutcomeName
    winner_id: uuid.UUID | None = None


def _located_span(
    candidate: EditCandidate, document_lines: Sequence[str]
) -> tuple[int, int] | None:
    """The quote's span on its own markdown line, or None when it is not unique.

    A quote the line carries twice is as good as absent here: the edit cannot
    be tied to characters, so it is reported instead of guessed at.
    """
    line = candidate.edit.start_line
    if line < 1 or line > len(document_lines):
        return None
    spans = locate_in_paragraph(
        document_lines[line - 1], normalize_whitespace(candidate.edit.original_text)
    )
    return spans[0] if len(spans) == 1 else None


def winner_sort_key(candidate: EditCandidate) -> tuple[int, int, float, str]:
    """Sort key picking the edit to keep: an accepted edit first, then the
    higher severity, then the older issue, then the lower id.

    The whole policy lives here so that every place two edits compete -- the
    per-line resolution below and the per-Word-paragraph pass the export runs
    once the lines have been mapped -- keeps the same edit, whatever order the
    rows arrived in.
    """
    created = candidate.issue_created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return (
        0 if candidate.edit.status == IssueEditStatus.ACCEPTED else 1,
        -candidate.issue_severity.sort_index(),
        created.timestamp(),
        str(candidate.edit.id),
    )


def pick_winner(candidates: Sequence[EditCandidate]) -> EditCandidate:
    """The one edit of a competing group to keep, per `winner_sort_key`."""
    return min(candidates, key=winner_sort_key)


def overlap_groups[T, K: (int, str)](
    items: Sequence[T],
    key: Callable[[T], K],
    span: Callable[[T], tuple[int, int]],
    item_id: Callable[[T], str],
) -> list[list[T]]:
    """Group items whose spans overlap, transitively, within each `key`.

    Both places two edits compete use this: the markdown lines here, and the
    Word paragraphs the export maps those lines to. Walking a key's spans in
    start order is enough: a group is closed as soon as a span starts at or
    after the furthest end reached so far. Ties sort by `item_id`, so the
    groups do not depend on the order the items arrive in.
    """
    by_key: dict[K, list[T]] = {}
    for item in items:
        by_key.setdefault(key(item), []).append(item)

    groups: list[list[T]] = []
    for group_key in sorted(by_key):
        ordered = sorted(
            by_key[group_key], key=lambda item: (span(item), item_id(item))
        )
        current: list[T] = []
        reach = -1
        for item in ordered:
            start, end = span(item)
            if current and start < reach:
                current.append(item)
                reach = max(reach, end)
                continue
            if current:
                groups.append(current)
            current = [item]
            reach = end
        if current:
            groups.append(current)
    return groups


def resolve_edit_conflicts(
    candidates: Sequence[EditCandidate], document_lines: Sequence[str]
) -> list[EditDecision]:
    """Decide, for every candidate, whether it can be applied to the document.

    Rejected edits are reported as such and never compete. An edit whose quote
    cannot be pinned to exactly one span of its line is ``unlocatable``. Of
    every group of edits whose spans overlap, one wins and the rest are
    ``conflict`` -- that includes duplicate proposals, which overlap exactly.

    Returned in line then span then id order, so the result does not depend on
    the order the rows came in.
    """
    decisions: list[EditDecision] = []
    located: list[EditCandidate] = []
    spans: dict[uuid.UUID, tuple[int, int]] = {}

    for candidate in candidates:
        edit = candidate.edit
        if edit.status == IssueEditStatus.REJECTED:
            decisions.append(
                EditDecision(
                    edit_id=edit.id, line=edit.start_line, span=None, outcome="rejected"
                )
            )
            continue
        span = _located_span(candidate, document_lines)
        if span is None:
            decisions.append(
                EditDecision(
                    edit_id=edit.id,
                    line=edit.start_line,
                    span=None,
                    outcome="unlocatable",
                )
            )
            continue
        spans[edit.id] = span
        located.append(candidate)

    groups = overlap_groups(
        located,
        key=lambda candidate: candidate.edit.start_line,
        span=lambda candidate: spans[candidate.edit.id],
        item_id=lambda candidate: str(candidate.edit.id),
    )
    for group in groups:
        winner = pick_winner(group)
        for member in group:
            is_winner = member.edit.id == winner.edit.id
            decisions.append(
                EditDecision(
                    edit_id=member.edit.id,
                    line=member.edit.start_line,
                    span=spans[member.edit.id],
                    outcome="apply" if is_winner else "conflict",
                    winner_id=None if is_winner else winner.edit.id,
                )
            )

    return sorted(
        decisions,
        key=lambda decision: (
            decision.line,
            decision.span[0] if decision.span else -1,
            str(decision.edit_id),
        ),
    )
