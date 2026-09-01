"""Extract embedded data-URI images from converted markdown to disk.

markitdown (via mammoth) inlines DOCX images as base64 data URIs. Keeping those
in the stored markdown would bloat the ``files.markdown`` column and every LLM
prompt, so main-document conversion extracts the bytes to disk and rewrites
each src to a ``draftdetective://{file_id}`` reference, addressed by the
``files`` row the caller persists for it (role EXTRACTED_IMAGE). The scheme
keeps persisted markdown independent of API routing: each consumer resolves it
to its own retrieval mechanism (the frontend to the download endpoint, agents
to an image tool). A rewrite never adds or removes lines: each image stays on
the single markdown line mammoth produced, which is what keeps issue line
anchors, ``#L`` links and the DOCX comment export valid.
"""

import base64
import binascii
import logging
import os
import re
import uuid
from typing import Optional

import aiofiles
from pydantic import BaseModel, Field
from xxhash import xxh128

from lib.config.env import config
from lib.services.docx.image_display_sizes import DisplaySizes

logger = logging.getLogger(__name__)

EXTRACTED_IMAGES_DIRNAME = "extracted_images"

# A full data-URI image as markitdown emits it with keep_data_uris=True.
# Legacy truncated stubs (`data:image/png;base64...`) have no comma and no
# base64 payload, so they never match and pass through untouched.
_DATA_URI_IMAGE_RE = re.compile(
    r"!\[(?P<alt>[^\]\n]*)\]"
    r"\(data:(?P<mime>image/[\w.+-]+);base64,(?P<data>[A-Za-z0-9+/=]+)"
    r"(?P<title> \"[^\"\n]*\")?\)"
)

_MIME_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/webp": ".webp",
    "image/tiff": ".tiff",
    "image/svg+xml": ".svg",
    # Metafiles are normally rendered to PNG upstream (drawing rasterization);
    # these land here only when that step was skipped. Browsers can't render
    # them, so the viewer shows the alt-text fallback.
    "image/emf": ".emf",
    "image/x-emf": ".emf",
    "image/wmf": ".wmf",
    "image/x-wmf": ".wmf",
}


class ExtractedImage(BaseModel):
    """Metadata for one image written to disk.

    ``id`` is generated here so the markdown can reference the image's future
    ``files`` row before it exists; the caller persists the row under this id.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    image_path: str
    mime_type: str
    file_size: int
    content_hash: str
    line_number: int
    alt: str = ""


class ImageExtractionResult(BaseModel):
    markdown: str
    images: list[ExtractedImage]


# Storage-agnostic reference scheme used in persisted markdown. Never a URL:
# consumers translate it (the document viewers to the file-download endpoint,
# agents to their image tool), so API routes can move without touching rows.
IMAGE_REFERENCE_SCHEME = "draftdetective://"


def image_reference(
    image_file_id: uuid.UUID | str, display_size: Optional[tuple[int, int]] = None
) -> str:
    """The src the rewritten markdown carries for an image's ``files`` row.

    The display size rides along as query parameters rather than as a raw
    ``<img>`` tag: a markdown image stays wrapped in a paragraph, which is
    what the viewers hang line numbers and issue anchoring on.
    """
    reference = f"{IMAGE_REFERENCE_SCHEME}{image_file_id}"
    if display_size and display_size[0] > 0 and display_size[1] > 0:
        reference += f"?w={display_size[0]}&h={display_size[1]}"
    return reference


async def extract_data_uri_images(
    markdown: str, display_sizes: Optional[DisplaySizes] = None
) -> ImageExtractionResult:
    """Extract every full data-URI image in ``markdown`` to disk.

    Returns the markdown with each extracted image's src rewritten to
    ``image_reference`` plus the metadata needed to persist the images as
    ``files`` rows. Images whose display size is known (``display_sizes``,
    read from the source DOCX) carry it in the reference's query parameters
    so the viewer shows them at the size the document intended. Images that
    fail to decode are left untouched. Line count is preserved.
    """
    matches = list(_DATA_URI_IMAGE_RE.finditer(markdown))
    if not matches:
        return ImageExtractionResult(markdown=markdown, images=[])

    images_dir = os.path.join(config.FILE_UPLOADS_MOUNT_PATH, EXTRACTED_IMAGES_DIRNAME)
    os.makedirs(images_dir, exist_ok=True)

    images: list[ExtractedImage] = []
    pieces: list[str] = []
    cursor = 0
    for match in matches:
        try:
            content = base64.b64decode(match.group("data"), validate=True)
        except (binascii.Error, ValueError):
            logger.warning(
                "Skipping undecodable data-URI image at markdown line %d",
                markdown.count("\n", 0, match.start()) + 1,
            )
            continue

        mime_type = match.group("mime")
        image_path, content_hash = await _write_image(images_dir, content, mime_type)
        size = display_sizes.take(content_hash) if display_sizes else None

        image = ExtractedImage(
            image_path=image_path,
            mime_type=mime_type,
            file_size=len(content),
            content_hash=content_hash,
            line_number=markdown.count("\n", 0, match.start()) + 1,
            alt=match.group("alt"),
        )
        images.append(image)

        title = match.group("title") or ""
        replacement = (
            f"![{image.alt}]({image_reference(image.id, size)}{title})"
        )
        pieces.append(markdown[cursor : match.start()])
        pieces.append(replacement)
        cursor = match.end()

    pieces.append(markdown[cursor:])
    logger.info("Extracted %d embedded image(s) from markdown", len(images))
    return ImageExtractionResult(markdown="".join(pieces), images=images)


async def _write_image(
    images_dir: str, content: bytes, mime_type: str
) -> tuple[str, str]:
    """Write image bytes content-addressed; reuse the file when it exists.

    Returns ``(image_path, content_hash)``.
    """
    content_hash = xxh128(content).hexdigest()
    extension = _MIME_EXTENSIONS.get(mime_type, ".bin")
    image_path = os.path.join(images_dir, content_hash + extension)

    if not os.path.exists(image_path):
        async with aiofiles.open(image_path, "wb") as f:
            await f.write(content)
    return image_path, content_hash
