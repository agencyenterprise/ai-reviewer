"""Persistence for images extracted from uploaded documents.

Extracted images live in the ``files`` table like every other on-disk binary,
under role EXTRACTED_IMAGE with ``parent_file_id`` pointing at the document
they came from. They are served by the regular file-download endpoint and are
deleted with their parent (FK cascade for the rows, ``delete_project_files``
for the disk files).
"""

import os
import uuid
from typing import List

from sqlalchemy import delete, select
from sqlmodel import col

from lib.config.database import get_async_db_session
from lib.models.file import File, FileRole
from lib.services.files import get_file_by_id
from lib.services.image_extraction import ExtractedImage
from lib.services.uuid_utils import ensure_uuid


async def replace_extracted_images(
    parent_file_id: uuid.UUID | str, images: List[ExtractedImage]
) -> None:
    """Replace the extracted-image rows for a file.

    Wholesale replacement keeps reconversion idempotent: the parent's markdown
    references images by the ids generated at extraction time, so rows from a
    previous conversion must never survive alongside new ones.
    """
    parent = await get_file_by_id(parent_file_id)

    async with get_async_db_session() as session:
        await session.execute(
            delete(File).where(col(File.parent_file_id) == parent.id)
        )
        for position, image in enumerate(images):
            extension = os.path.splitext(image.image_path)[1]
            session.add(
                File(
                    id=image.id,
                    project_id=parent.project_id,
                    file_name=f"image-{position + 1}{extension}",
                    file_path=image.image_path,
                    file_type=image.mime_type,
                    file_size=image.file_size,
                    content_hash=image.content_hash,
                    role=FileRole.EXTRACTED_IMAGE,
                    uploaded_by=parent.uploaded_by,
                    description=image.alt or None,
                    revision=parent.revision,
                    parent_file_id=parent.id,
                    line_number=image.line_number,
                )
            )
        await session.commit()


async def get_extracted_images(parent_file_id: uuid.UUID | str) -> List[File]:
    """Return a file's extracted images, ordered by position in the markdown."""
    normalized_parent_id = ensure_uuid(parent_file_id, "file ID")

    async with get_async_db_session() as session:
        stmt = (
            select(File)
            .where(
                col(File.parent_file_id) == normalized_parent_id,
                col(File.role) == FileRole.EXTRACTED_IMAGE,
            )
            .order_by(col(File.line_number))
        )
        return list((await session.execute(stmt)).scalars().all())
