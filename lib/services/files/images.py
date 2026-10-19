"""Persistence for images extracted from uploaded documents.

Extracted images live in the ``files`` table like every other on-disk binary,
under role EXTRACTED_IMAGE with ``parent_file_id`` pointing at the document
they came from. They are served by the regular file-download endpoint and are
deleted with their parent (FK cascade for the rows, ``delete_project_files``
for the disk files).

Images from a document read in a conversation, the Word add-in's chat or Teams, have
no parent file: they belong to that conversation (``conversation_id``) instead of a
project.
"""

import os
import re
import uuid

from sqlalchemy import ColumnElement, and_, delete, select
from sqlmodel import col

from lib.config.database import get_async_db_session
from lib.models.file import File, FileRole
from lib.services.files.service import (
    _delete_file_from_disk,
    _is_path_shared,
    get_file_by_id,
)
from lib.services.image_extraction import IMAGE_REFERENCE_SCHEME, ExtractedImage

_REFERENCE = re.compile(
    re.escape(IMAGE_REFERENCE_SCHEME)
    + r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


async def replace_extracted_images(
    parent_file_id: uuid.UUID | str, images: list[ExtractedImage]
) -> None:
    """Replace the extracted-image rows for a file.

    Wholesale replacement keeps reconversion idempotent: the parent's markdown
    references images by the ids generated at extraction time, so rows from a
    previous conversion must never survive alongside new ones. Their disk
    files go too when nothing references them anymore — cleanup discovers
    disk files only through rows, so skipping this would strand them forever
    when a reconversion produces different bytes (e.g. rendering changed).
    """
    parent = await get_file_by_id(parent_file_id)
    rows = [
        File(
            id=image.id,
            project_id=parent.project_id,
            file_name=_name(position, image),
            file_path=image.image_path,
            file_type=image.mime_type,
            file_size=image.file_size,
            content_hash=image.content_hash,
            role=FileRole.EXTRACTED_IMAGE,
            uploaded_by=parent.uploaded_by,
            description=image.alt or None,
            revision=parent.revision,
            parent_file_id=parent.id,
        )
        for position, image in enumerate(images)
    ]
    await _replace(col(File.parent_file_id) == parent.id, rows)


async def add_conversation_images(
    conversation_id: uuid.UUID, images: list[ExtractedImage]
) -> None:
    """Keep the images of a document read in a conversation, the Word chat's or Teams'.

    Added rather than replaced. A Teams conversation can hold several documents (two
    revisions, two files), and opening one must not unlink the other's. The Word chat
    sends its document again whenever it changes, and markdown already stored (a turn
    that failed before the new document was) must still find the images it names.
    Re-reading a document adds its images again under new ids; the disk files are
    shared, being content-addressed, and the rows go with the conversation. The Word
    chat drops the ones no document it holds names (``prune_conversation_images``), and
    Teams the ones of a copy it replaces (``drop_conversation_images``).
    """

    async with get_async_db_session() as session:
        for row in _conversation_rows(conversation_id, images):
            session.add(row)
        await session.commit()


def referenced_images(markdown: str) -> set[uuid.UUID]:
    """The ids of the images ``markdown`` names by their ``draftdetective://`` src."""

    return {uuid.UUID(match) for match in _REFERENCE.findall(markdown)}


async def prune_conversation_images(
    conversation_id: uuid.UUID, keep: set[uuid.UUID]
) -> None:
    """Drop the conversation's images ``keep`` does not name, files included once unused.

    For a conversation about one document that it sends again as it changes, the Word
    chat's: each copy adds its images under new ids, and only the copy the conversation
    holds now names any of them.
    """

    await _replace(
        and_(
            col(File.conversation_id) == conversation_id,
            col(File.id).not_in(keep),
        ),
        [],
    )


async def drop_conversation_images(
    conversation_id: uuid.UUID, ids: set[uuid.UUID]
) -> None:
    """Drop these images of the conversation, files included once unused."""

    if ids:
        await _replace(
            and_(
                col(File.conversation_id) == conversation_id,
                col(File.id).in_(ids),
            ),
            [],
        )


def _conversation_rows(
    conversation_id: uuid.UUID, images: list[ExtractedImage]
) -> list[File]:
    return [
        File(
            id=image.id,
            conversation_id=conversation_id,
            file_name=_name(position, image),
            file_path=image.image_path,
            file_type=image.mime_type,
            file_size=image.file_size,
            content_hash=image.content_hash,
            role=FileRole.EXTRACTED_IMAGE,
            description=image.alt or None,
        )
        for position, image in enumerate(images)
    ]


def _name(position: int, image: ExtractedImage) -> str:
    return f"image-{position + 1}{os.path.splitext(image.image_path)[1]}"


async def _replace(owned: ColumnElement[bool], rows: list[File]) -> None:
    """Delete the rows ``owned`` selects, insert ``rows``, then drop orphaned files."""

    incoming_paths = {row.file_path for row in rows}
    async with get_async_db_session() as session:
        previous_stmt = select(File).where(owned)
        previous = [
            (row.file_path, row.id)
            for row in (await session.execute(previous_stmt)).scalars()
        ]

        await session.execute(delete(File).where(owned))

        stale_paths: list[str] = []
        for path, row_id in previous:
            # The new rows are not inserted yet, so paths they will reference
            # must be treated as still in use.
            if path in incoming_paths:
                continue
            if not await _is_path_shared(session, path, row_id):
                stale_paths.append(path)

        for row in rows:
            session.add(row)
        await session.commit()

    # Disk cleanup strictly after the commit: a failed transaction restores
    # the old rows, and restored rows must never point at deleted files.
    for path in stale_paths:
        _delete_file_from_disk(path)
