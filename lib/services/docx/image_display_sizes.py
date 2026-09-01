"""Read the display size Word gives each embedded image.

A DOCX stores an image's *display* dimensions (EMU) separately from the image
bytes — a high-resolution logo is often shown small. mammoth drops those
dimensions during conversion, so extraction reads them here, straight from the
inline shapes, and matches them to extracted images by content hash: mammoth
base64-encodes the image part's bytes verbatim, so the hash of the part blob
equals the hash of the decoded data URI.
"""

import logging
from collections import deque

from docx import Document
from docx.oxml.ns import qn
from xxhash import xxh128

logger = logging.getLogger(__name__)

EMU_PER_CSS_PIXEL = 9525  # 914400 EMU per inch / 96 CSS px per inch


class DisplaySizes:
    """Display sizes queued per content hash, consumed in document order.

    The same image can appear more than once at different sizes (e.g. a logo
    in a header and a footer); both the inline shapes and the converted
    markdown list occurrences in document order, so a FIFO per hash pairs
    them correctly.
    """

    def __init__(self) -> None:
        self._sizes: dict[str, deque[tuple[int, int]]] = {}

    def add(self, content_hash: str, width_px: int, height_px: int) -> None:
        self._sizes.setdefault(content_hash, deque()).append((width_px, height_px))

    def take(self, content_hash: str) -> tuple[int, int] | None:
        """Pop the next size for this content, or None when unknown."""
        queue = self._sizes.get(content_hash)
        if not queue:
            return None
        return queue.popleft()


def read_docx_image_display_sizes(docx_path: str) -> DisplaySizes:
    """Map each embedded image's content hash to its display size in CSS px.

    Walks every ``w:drawing`` in the body XML rather than
    ``document.inline_shapes`` so anchored (floating) images — cover-page
    logos, for instance — get sizes too. Any parse failure returns an empty
    map: sizes are an enhancement, never a reason to fail a conversion.
    """
    sizes = DisplaySizes()
    try:
        document = Document(docx_path)
        for drawing in document.element.body.iter(qn("w:drawing")):
            extent = drawing.find(f".//{qn('wp:extent')}")
            blip = drawing.find(f".//{qn('a:blip')}")
            if extent is None or blip is None:
                continue
            embed_id = blip.get(qn("r:embed"))
            if not embed_id:
                continue
            try:
                blob = document.part.related_parts[embed_id].blob
            except KeyError:
                continue
            sizes.add(
                xxh128(blob).hexdigest(),
                round(int(extent.get("cx", "0")) / EMU_PER_CSS_PIXEL),
                round(int(extent.get("cy", "0")) / EMU_PER_CSS_PIXEL),
            )
    except Exception:
        logger.warning(
            "Could not read image display sizes from %s", docx_path, exc_info=True
        )
    return sizes
