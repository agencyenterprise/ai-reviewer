"""Mount a review request's documents on the agent filesystem.

Each document gets its own folder under ``/inputs/``, numbered in the order the
author gave them:

- ``document.md``: the document's text, as converted from the upload
- ``comments.md``: its Word comment threads, when it is a DOCX that has any
- ``tracked-changes.md``: its tracked insertions and deletions, likewise

``/inputs/index.md`` lists every folder with what the upload itself says (file
name, the DOCX's author and dates, how many comments and changes it carries),
which is the agent's starting point for working out what each document is.
"""

import asyncio
import logging
import re
from typing import Any, List, Optional

from deepagents.backends.utils import create_file_data
from pydantic import BaseModel

from lib.services.docx.review_markup import DocxReviewMarkup, read_docx_review_markup
from lib.services.docx.review_markup_markdown import (
    comments_markdown,
    tracked_changes_markdown,
    visible_changes,
)
from lib.services.file import FileDocument
from lib.workflows.review_assistant.state import ReviewAssistantInput

logger = logging.getLogger(__name__)

INPUTS_ROOT = "/inputs"
INPUTS_INDEX_PATH = f"{INPUTS_ROOT}/index.md"


class MountedInputs(BaseModel):
    inputs: List[ReviewAssistantInput]
    files: dict[str, Any]


def _slug(file_name: str) -> str:
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", file_name)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", stem).strip("-").lower()
    return slug[:60] or "document"


def _is_docx(document: FileDocument) -> bool:
    return any(
        name.lower().endswith(".docx") for name in (document.file_name, document.file_path)
    )


async def _read_markup(document: FileDocument) -> Optional[DocxReviewMarkup]:
    """The DOCX's comments and tracked changes, or None for other formats.

    A file that will not parse loses only its markup: its text is still read.
    """
    if not _is_docx(document):
        return None
    try:
        return await asyncio.to_thread(read_docx_review_markup, document.file_path)
    except Exception as error:
        logger.warning("Could not read comments from %s: %s", document.file_name, error)
        return None


def _index_entry(entry: ReviewAssistantInput, markup: Optional[DocxReviewMarkup]) -> str:
    lines = [f"## {entry.folder}", "", f"- File name: {entry.file_name}"]
    if markup is not None:
        properties = markup.properties
        for label, value in (
            ("Author (file properties)", properties.author),
            ("Last saved by", properties.last_modified_by),
            ("Created", properties.created),
            ("Last modified", properties.modified),
        ):
            if value:
                lines.append(f"- {label}: {value}")
    lines.append(f"- Text: `{entry.folder}/document.md`")
    if entry.comment_count:
        lines.append(
            f"- Comments: {entry.comment_count} thread(s), in `{entry.folder}/comments.md`"
        )
    if entry.tracked_change_count:
        lines.append(
            f"- Tracked changes: {entry.tracked_change_count}, in "
            f"`{entry.folder}/tracked-changes.md`"
        )
    return "\n".join(lines)


async def mount_review_inputs(documents: List[FileDocument]) -> MountedInputs:
    """Build the ``/inputs/`` tree for these documents."""
    files: dict[str, Any] = {}
    inputs: List[ReviewAssistantInput] = []
    index_entries: List[str] = []

    for number, document in enumerate(documents, start=1):
        folder = f"{INPUTS_ROOT}/{number:02d}-{_slug(document.file_name)}"
        files[f"{folder}/document.md"] = create_file_data(document.markdown)

        markup = await _read_markup(document)
        comments = comments_markdown(document.file_name, markup) if markup else None
        changes = tracked_changes_markdown(document.file_name, markup) if markup else None
        if comments:
            files[f"{folder}/comments.md"] = create_file_data(comments)
        if changes:
            files[f"{folder}/tracked-changes.md"] = create_file_data(changes)

        entry = ReviewAssistantInput(
            file_id=document.file_id,
            file_name=document.file_name,
            folder=folder,
            comment_count=len(markup.comments) if markup else 0,
            tracked_change_count=len(visible_changes(markup)) if markup else 0,
        )
        inputs.append(entry)
        index_entries.append(_index_entry(entry, markup))

    index = "\n\n".join(
        [
            "# Inputs",
            f"{len(inputs)} document(s), in the order the author gave them. "
            "Nobody has said what each one is: work that out from its content.",
            *index_entries,
        ]
    )
    files[INPUTS_INDEX_PATH] = create_file_data(index + "\n")
    return MountedInputs(inputs=inputs, files=files)
