"""Read how Word places each embedded image: its display size and its crop.

A DOCX stores an image's *display* dimensions (EMU) separately from the image
bytes — a high-resolution logo is often shown small. It can also crop the
image (``a:srcRect``), in which case the display box describes the *cropped*
region, not the whole picture. mammoth drops both during conversion, so
extraction reads them here, straight from the body's drawing XML (inline and
anchored alike), and matches them to extracted images by content hash: mammoth
base64-encodes the image part's bytes verbatim, so the hash of the part blob
equals the hash of the decoded data URI.

Size and crop travel together on purpose: honouring one without the other is
what squashes a cropped figure into a box shaped for a region it no longer
matches.
"""

import logging
from collections import deque
from typing import Optional

from docx import Document
from docx.oxml.ns import qn
from pydantic import BaseModel
from xxhash import xxh128

logger = logging.getLogger(__name__)

EMU_PER_CSS_PIXEL = 9525  # 914400 EMU per inch / 96 CSS px per inch

# ``a:srcRect`` edges are ST_Percentage: integer thousandths of a percent
# ("17222" is 17.222%), or a literal percentage string in the strict schema.
_PERCENTAGE_UNITS_PER_WHOLE = 100_000


class SourceRect(BaseModel):
    """Fractions of a picture inset on each edge (``a:srcRect``).

    Word keeps the full image bytes in the package and crops at display time,
    so an extracted image is the *uncropped* picture while the drawing's
    extent describes the cropped region.

    An edge can be negative, which is an outset: Word pads that side rather
    than trimming it, so the extent covers area the image does not contain.
    Signs are kept rather than clamped — clamping a negative edge on its own
    silently reshapes the region (``l="-10000" r="10000"`` describes a
    full-width band shifted left, not a 90%-wide crop), which would put the
    wrong pixels under a size that claims to describe them.
    """

    left: float = 0.0
    top: float = 0.0
    right: float = 0.0
    bottom: float = 0.0
    unreadable: bool = False
    """An edge the document declared but that could not be parsed."""

    @property
    def is_applicable(self) -> bool:
        """Whether this region can be reproduced by cropping the picture.

        False for three kinds of region, which all mean the extent describes
        something the stored bytes cannot be trimmed to. Callers store the
        picture whole and declare no size for it rather than guessing:

        * ``unreadable`` — an edge was declared but could not be parsed, so
          the real region is unknown;
        * an outset — a negative edge, where Word pads that side instead of
          trimming it;
        * overlapping insets, which leave no region at all.
        """
        if self.unreadable:
            return False
        if min(self.left, self.top, self.right, self.bottom) < 0:
            return False
        return self.left + self.right < 1.0 and self.top + self.bottom < 1.0

    def crop_box(self, width: int, height: int) -> Optional[tuple[int, int, int, int]]:
        """The ``(left, top, right, bottom)`` pixel box to crop to.

        None when this region trims nothing at this resolution: either an
        untrimmed rect, or — on a picture a handful of pixels wide — a trim
        that rounds away entirely. Callers keep the image as it is.

        Rects that are not ``is_applicable`` must be rejected before calling
        this; it assumes the region is a genuine crop, so a ``None`` here
        never means "this crop was impossible".
        """
        box = (
            round(width * self.left),
            round(height * self.top),
            width - round(width * self.right),
            height - round(height * self.bottom),
        )
        if box[0] >= box[2] or box[1] >= box[3]:
            return None
        if box == (0, 0, width, height):
            return None
        return box


class ImagePlacement(BaseModel):
    """How one occurrence of an image is displayed in the document."""

    width_px: int
    height_px: int
    crop: Optional[SourceRect] = None


class DisplaySizes:
    """Placements queued per content hash, consumed in document order.

    The same image can appear more than once in the body at different sizes
    (e.g. a figure repeated as a thumbnail, or the same photo cropped two
    ways); both the body's drawing XML and the converted markdown list
    occurrences in document order, so a FIFO per hash pairs them correctly.
    """

    def __init__(self) -> None:
        self._placements: dict[str, deque[ImagePlacement]] = {}

    def add(self, content_hash: str, placement: ImagePlacement) -> None:
        self._placements.setdefault(content_hash, deque()).append(placement)

    def take(self, content_hash: str) -> Optional[ImagePlacement]:
        """Pop the next placement for this content, or None when unknown."""
        queue = self._placements.get(content_hash)
        if not queue:
            return None
        return queue.popleft()


def _crop_fraction(value: Optional[str]) -> Optional[float]:
    """One ``a:srcRect`` edge as a signed fraction, or None if unparseable.

    A missing or empty attribute is simply an untrimmed edge. A *present*
    but malformed one is a parse failure and returns None: reading it as
    zero would report a cropped picture as uncropped, and the declared size
    would then stretch the whole image.

    Negative values are kept: they mark an outset, which ``SourceRect``
    reports through ``is_applicable`` so the region is not taken for a crop.
    """
    if not value:
        return 0.0
    text = value.strip()
    if not text:
        return 0.0
    try:
        return (
            float(text[:-1]) / 100
            if text.endswith("%")
            else int(text) / _PERCENTAGE_UNITS_PER_WHOLE
        )
    except ValueError:
        return None


def _read_source_rect(blip) -> Optional[SourceRect]:
    """The crop declared alongside ``blip``, or None when it is uncropped.

    ``a:srcRect`` is a sibling of ``a:blip`` inside ``pic:blipFill``, so it is
    read from the parent rather than by searching the whole drawing — a
    drawing can hold more than one picture.
    """
    blip_fill = blip.getparent()
    src_rect = blip_fill.find(qn("a:srcRect")) if blip_fill is not None else None
    if src_rect is None:
        return None
    edges = {
        "left": _crop_fraction(src_rect.get("l")),
        "top": _crop_fraction(src_rect.get("t")),
        "right": _crop_fraction(src_rect.get("r")),
        "bottom": _crop_fraction(src_rect.get("b")),
    }
    if any(fraction is None for fraction in edges.values()):
        # The picture is cropped by an amount we cannot determine. Reporting
        # it as uncropped would pair whole bytes with a size describing a
        # region of them.
        logger.warning("Unparseable a:srcRect edge in %s", src_rect.attrib)
        return SourceRect(unreadable=True)
    crop = SourceRect.model_validate(edges)
    if not any(edges.values()):
        return None  # Word writes an empty srcRect for uncropped pictures.
    return crop


def read_docx_image_display_sizes(docx_path: str) -> DisplaySizes:
    """Map each embedded image's content hash to how the document places it.

    Walks every ``w:drawing`` in the body XML rather than
    ``document.inline_shapes`` so anchored (floating) images — cover-page
    logos, for instance — get placements too. Any parse failure returns an
    empty map: placements are an enhancement, never a reason to fail a
    conversion.
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
                ImagePlacement(
                    width_px=round(int(extent.get("cx", "0")) / EMU_PER_CSS_PIXEL),
                    height_px=round(int(extent.get("cy", "0")) / EMU_PER_CSS_PIXEL),
                    crop=_read_source_rect(blip),
                ),
            )
    except Exception:
        logger.warning(
            "Could not read image display sizes from %s", docx_path, exc_info=True
        )
    return sizes
