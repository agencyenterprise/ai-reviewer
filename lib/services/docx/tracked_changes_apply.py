"""Writing the planned redlines into a DOCX, as Word tracked changes.

The comment pass tells an author what is wrong; this pass offers the fix as a
``w:del`` + ``w:ins`` pair, so the author can accept or reject each proposed
edit where they are already reading the document.

Ordering is not a preference. python-docx paragraph text stops carrying
inserted and deleted runs once tracked changes exist, so the paragraph index
map the comment pass anchors to is only valid before this pass runs: comments
first, save, then redlines.

The instructions come from `lib.services.docx.tracked_changes_planning`, which
resolved every one of them against the original file. The comments are written
before anything is known about the write, so a caller whose write was refused
somewhere writes the file again; see `lib.services.docx.edit_export`.
"""

import asyncio
import logging
from collections.abc import Sequence

from docx_editor import BatchOperationError, EditOperation, EditResult
from docx_editor import Document as EditorDocument

from lib.services.docx.tracked_changes_models import (
    TRACKED_CHANGE_AUTHOR,
    EditOutcome,
    PlannedEdit,
    editor_workspace,
)

logger = logging.getLogger(__name__)


def _failed(edits: Sequence[PlannedEdit], reason: str) -> list[EditOutcome]:
    return [
        EditOutcome(edit_id=edit.edit_id, status="failed", detail=reason)
        for edit in edits
    ]


def _outcome(edit: PlannedEdit, ref: str, result: EditResult) -> EditOutcome:
    # No revision group means docx-editor wrote nothing -- the operation was a
    # no-op, or it spliced into text an earlier one inserted. Either way there
    # is no redline for the author to accept, so the edit did not apply however
    # quietly the call returned.
    if result.group_id is None:
        logger.warning(
            "Tracked change for edit %s in paragraph %s created no revision "
            "group -- it may have spliced into an earlier insertion",
            edit.edit_id,
            ref,
        )
        return EditOutcome(
            edit_id=edit.edit_id,
            status="failed",
            detail="the change produced no tracked revision in Word",
        )
    return EditOutcome(edit_id=edit.edit_id, status="applied")


def _operations(
    by_paragraph: dict[str, list[PlannedEdit]],
) -> tuple[dict[str, list[EditOperation]], dict[str, list[EditOutcome]]]:
    """Each paragraph's operations, back-to-front, or why it has none.

    Back-to-front: docx-editor matches each operation against the paragraph as
    it stands, so doing the later spans first leaves the earlier ones' offsets
    and occurrence counts untouched. docx-editor validates an operation's own
    arguments when it is built, and a ``ValueError`` there costs only that
    paragraph its redlines.
    """
    operations: dict[str, list[EditOperation]] = {}
    refused: dict[str, list[EditOutcome]] = {}
    for ref, edits in by_paragraph.items():
        try:
            operations[ref] = [
                EditOperation.replace(
                    edit.find,
                    edit.replace_with,
                    paragraph=ref,
                    occurrence=edit.occurrence,
                )
                for edit in edits
            ]
        except ValueError as error:
            refused[ref] = _failed(edits, str(error))
    return operations, refused


def _apply_document(
    doc: EditorDocument, by_paragraph: dict[str, list[PlannedEdit]]
) -> dict[str, list[EditOutcome]]:
    """Write every paragraph's redlines in one batch, per paragraph outcomes.

    One batch for the whole document rather than one per paragraph: docx-editor
    snapshots the entire document before each batch so it can roll back, and
    on a long report that snapshot, taken once per paragraph, was nearly all of
    the export's time. A paragraph the library refuses still costs only its own
    redlines -- the batch rolls back, that paragraph's edits are reported as
    ``failed`` with the reason given, and the rest is written again without it.
    """
    operations, outcomes = _operations(by_paragraph)
    while operations:
        flat = [(ref, op) for ref, ops in operations.items() for op in ops]
        try:
            results = doc.batch_edit([op for _, op in flat])
        except BatchOperationError as error:
            ref = flat[error.operation_index][0]
            logger.warning(
                "Tracked changes for paragraph %s were rejected: %s", ref, error.reason
            )
            outcomes[ref] = _failed(by_paragraph[ref], error.reason)
            del operations[ref]
            continue
        written = iter(results)
        for ref in operations:
            outcomes[ref] = [
                _outcome(edit, ref, next(written)) for edit in by_paragraph[ref]
            ]
        break
    return outcomes


def _apply_sync(
    docx_path: str,
    planned: Sequence[PlannedEdit],
    author: str,
    workspace_root: str | None,
) -> list[EditOutcome]:
    by_paragraph: dict[str, list[PlannedEdit]] = {}
    for edit in planned:
        by_paragraph.setdefault(edit.paragraph_ref, []).append(edit)
    for edits in by_paragraph.values():
        edits.sort(key=lambda edit: edit.span, reverse=True)

    with editor_workspace(workspace_root) as workspace:
        doc = EditorDocument.open(docx_path, author=author, workspace_dir=workspace)
        try:
            outcomes = _apply_document(doc, by_paragraph)
            doc.save()
        finally:
            doc.close()
    return [outcome for ref in sorted(outcomes) for outcome in outcomes[ref]]


async def apply_tracked_changes(
    docx_path: str,
    planned: Sequence[PlannedEdit],
    author: str = TRACKED_CHANGE_AUTHOR,
    workspace_root: str | None = None,
) -> list[EditOutcome]:
    """Write the planned redlines into `docx_path`, in place.

    The refs a plan carries were computed on the original file and stay valid
    here: they are anchored to a hash of the paragraph's visible text, which
    adding Word comments does not change. A paragraph docx-editor rejects
    leaves the rest of the document redlined: its edits come back as
    ``failed`` and the others are written without it.
    """
    if not planned:
        return []
    return await asyncio.to_thread(
        _apply_sync, docx_path, planned, author, workspace_root
    )
