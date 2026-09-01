"""Unit tests for `lib.services.image_extraction`.

The invariant that matters most is line preservation: extraction rewrites each
image src in place, and issue anchors, `#L` links and the DOCX comment export
all assume the stored markdown's line numbers never move.
"""

import base64
import io
import os
from unittest.mock import patch

import pytest
from PIL import Image
from xxhash import xxh128

from lib.services.docx.image_display_sizes import (
    DisplaySizes,
    ImagePlacement,
    SourceRect,
)
from lib.services.image_extraction import (
    EXTRACTED_IMAGES_DIRNAME,
    extract_data_uri_images,
    image_reference,
)

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
PNG_B64 = base64.b64encode(PNG_BYTES).decode()


def _uploads_patch(tmp_path):
    return patch(
        "lib.services.image_extraction.config.FILE_UPLOADS_MOUNT_PATH", str(tmp_path)
    )


@pytest.mark.asyncio
async def test_extracts_image_and_rewrites_src(tmp_path):
    markdown = f"Before.\n\n![Figure 1](data:image/png;base64,{PNG_B64})\n\nAfter."

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown)

    assert len(result.images) == 1
    image = result.images[0]
    assert image.mime_type == "image/png"
    assert image.file_size == len(PNG_BYTES)
    assert image.line_number == 3
    assert image.alt == "Figure 1"
    assert os.path.isfile(image.image_path)
    assert image.image_path.startswith(
        os.path.join(str(tmp_path), EXTRACTED_IMAGES_DIRNAME)
    )
    with open(image.image_path, "rb") as f:
        assert f.read() == PNG_BYTES

    expected_src = image_reference(image.id)
    assert expected_src == f"draftdetective://{image.id}"
    assert result.markdown == f"Before.\n\n![Figure 1]({expected_src})\n\nAfter."


@pytest.mark.asyncio
async def test_line_count_is_preserved(tmp_path):
    markdown = (
        f"# Title\n\n![](data:image/png;base64,{PNG_B64})\n\n"
        f"Middle paragraph.\n\n![alt text](data:image/png;base64,{PNG_B64})\n"
    )

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown)

    assert result.markdown.count("\n") == markdown.count("\n")
    assert [img.line_number for img in result.images] == [3, 7]


@pytest.mark.asyncio
async def test_identical_images_share_one_disk_file_but_not_an_id(tmp_path):
    markdown = (
        f"![a](data:image/png;base64,{PNG_B64})\n"
        f"![b](data:image/png;base64,{PNG_B64})\n"
    )

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown)

    assert len(result.images) == 2
    assert result.images[0].image_path == result.images[1].image_path
    assert result.images[0].content_hash == result.images[1].content_hash
    # Each occurrence gets its own files row, so its own id and markdown src.
    assert result.images[0].id != result.images[1].id


@pytest.mark.asyncio
async def test_legacy_truncated_stub_is_left_untouched(tmp_path):
    """Documents converted before extraction existed carry `base64...` stubs."""
    markdown = "Text.\n\n![old figure](data:image/png;base64...)\n"

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown)

    assert result.images == []
    assert result.markdown == markdown


@pytest.mark.asyncio
async def test_undecodable_payload_is_skipped(tmp_path):
    """A corrupt base64 payload must not abort extraction of the others."""
    markdown = (
        "![bad](data:image/png;base64,AAAA=BADPADDING)\n"
        f"![good](data:image/png;base64,{PNG_B64})\n"
    )

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown)

    assert len(result.images) == 1
    assert result.images[0].line_number == 2
    assert "![bad](data:image/png;base64,AAAA=BADPADDING)" in result.markdown
    assert f"![good]({image_reference(result.images[0].id)})" in result.markdown


@pytest.mark.asyncio
async def test_markdown_without_images_is_returned_verbatim(tmp_path):
    markdown = "# Just text\n\nNo images anywhere.\n"

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown)

    assert result.markdown == markdown
    assert result.images == []
    assert not os.path.exists(os.path.join(str(tmp_path), EXTRACTED_IMAGES_DIRNAME))


@pytest.mark.asyncio
async def test_known_display_size_emits_sized_img_tag(tmp_path):
    sizes = DisplaySizes()
    content_hash = xxh128(PNG_BYTES).hexdigest()
    sizes.add(content_hash, ImagePlacement(width_px=150, height_px=48))
    sizes.add(content_hash, ImagePlacement(width_px=75, height_px=24))
    markdown = (
        f"![logo](data:image/png;base64,{PNG_B64})\n\n"
        f"![logo small](data:image/png;base64,{PNG_B64})\n"
    )

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown, sizes)

    first, second = result.images
    # Sizes are consumed in document order, so the same image content can
    # appear at two different sizes. The size rides in the reference's query
    # parameters so the image stays a plain (paragraph-wrapped) markdown image.
    assert f"![logo](draftdetective://{first.id}?w=150&h=48)" in result.markdown
    assert f"![logo small](draftdetective://{second.id}?w=75&h=24)" in result.markdown
    assert result.markdown.count("\n") == markdown.count("\n")


@pytest.mark.asyncio
async def test_unknown_display_size_keeps_markdown_image(tmp_path):
    markdown = f"![fig](data:image/png;base64,{PNG_B64})\n"

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown, DisplaySizes())

    assert f"![fig](draftdetective://{result.images[0].id})" in result.markdown
    assert "?w=" not in result.markdown


@pytest.mark.asyncio
async def test_write_leaves_no_temp_artifacts(tmp_path):
    """Images land via a temp name + atomic rename; the temp file must not
    survive, and the store must hold only content-addressed files."""
    markdown = f"![a](data:image/png;base64,{PNG_B64})\n"

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown)

    images_dir = os.path.join(str(tmp_path), EXTRACTED_IMAGES_DIRNAME)
    on_disk = sorted(os.listdir(images_dir))
    assert on_disk == [os.path.basename(result.images[0].image_path)]
    assert not any(name.endswith(".tmp") for name in on_disk)


@pytest.mark.asyncio
async def test_existing_image_file_is_not_rewritten(tmp_path):
    """Content-addressed files are immutable: a second extraction of the same
    bytes must not touch the existing file (readers may be serving it)."""
    from unittest.mock import patch as mock_patch

    markdown = f"![a](data:image/png;base64,{PNG_B64})\n"
    with _uploads_patch(tmp_path):
        first = await extract_data_uri_images(markdown)

        with mock_patch("lib.services.image_extraction.os.replace") as replace_mock:
            second = await extract_data_uri_images(markdown)

    replace_mock.assert_not_called()
    assert second.images[0].image_path == first.images[0].image_path


def _png_of(width: int, height: int) -> bytes:
    """A gradient PNG, so a crop is detectable from the stored pixels."""
    image = Image.new("RGB", (width, height))
    image.putdata(
        [
            (x * 255 // max(width - 1, 1), y * 255 // max(height - 1, 1), 0)
            for y in range(height)
            for x in range(width)
        ]
    )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _markdown_for(png: bytes) -> str:
    return f"![fig](data:image/png;base64,{base64.b64encode(png).decode()})\n"


def _sizes_for(png: bytes, placement: ImagePlacement) -> DisplaySizes:
    sizes = DisplaySizes()
    sizes.add(xxh128(png).hexdigest(), placement)
    return sizes


@pytest.mark.asyncio
async def test_declared_crop_is_applied_to_the_stored_image(tmp_path):
    """Word crops at display time and keeps the whole picture in the package,
    so the extent describes a region the raw bytes do not match. Storing the
    picture uncropped is what squashed Figure 1 of a real report."""
    png = _png_of(750, 450)
    # 17.222% off the top and 3.597% off the bottom leaves a 750x357 region,
    # which is what the drawing's 624x297 extent is shaped for.
    placement = ImagePlacement(
        width_px=624, height_px=297, crop=SourceRect(top=0.17222, bottom=0.03597)
    )

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(
            _markdown_for(png), _sizes_for(png, placement)
        )

    image = result.images[0]
    with Image.open(image.image_path) as stored:
        assert stored.size == (750, 357)
        assert abs(stored.width / stored.height - 624 / 297) < 0.01
    assert f"?w=624&h=297" in result.markdown


@pytest.mark.asyncio
async def test_cropped_image_is_addressed_by_its_cropped_bytes(tmp_path):
    """The stored file is content-addressed by what lands on disk, not by the
    bytes Word embedded — otherwise the same picture cropped two ways would
    collide on one file."""
    png = _png_of(400, 400)
    sizes = DisplaySizes()
    content_hash = xxh128(png).hexdigest()
    sizes.add(
        content_hash,
        ImagePlacement(width_px=100, height_px=50, crop=SourceRect(bottom=0.5)),
    )
    sizes.add(
        content_hash,
        ImagePlacement(width_px=50, height_px=100, crop=SourceRect(right=0.5)),
    )
    markdown = _markdown_for(png) + _markdown_for(png)

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown, sizes)

    top, left = result.images
    assert top.content_hash != left.content_hash != content_hash
    assert top.image_path != left.image_path
    with Image.open(top.image_path) as stored:
        assert stored.size == (400, 200)
    with Image.open(left.image_path) as stored:
        assert stored.size == (200, 400)


@pytest.mark.asyncio
async def test_uncropped_image_is_stored_verbatim(tmp_path):
    """No crop means no re-encoding: identical bytes must keep deduplicating."""
    png = _png_of(300, 200)
    placement = ImagePlacement(width_px=150, height_px=100)

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(
            _markdown_for(png), _sizes_for(png, placement)
        )

    with open(result.images[0].image_path, "rb") as f:
        assert f.read() == png
    assert result.images[0].content_hash == xxh128(png).hexdigest()


@pytest.mark.asyncio
async def test_crop_too_small_to_change_a_pixel_leaves_bytes_untouched(tmp_path):
    """A sub-pixel crop must not force a re-encode, or content addressing
    would split one image into two files for no visible difference."""
    png = _png_of(100, 100)
    placement = ImagePlacement(
        width_px=100, height_px=100, crop=SourceRect(top=0.001, bottom=0.001)
    )

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(
            _markdown_for(png), _sizes_for(png, placement)
        )

    with open(result.images[0].image_path, "rb") as f:
        assert f.read() == png
    assert "?w=100&h=100" in result.markdown


@pytest.mark.asyncio
async def test_uncroppable_format_drops_the_declared_size(tmp_path):
    """The reference's `?w=&h=` describes the bytes on disk. When a crop
    cannot be applied, declaring the cropped region's size would stretch the
    uncropped image; the viewer's own proportions are the safer fallback."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
    markdown = f"![fig](data:image/svg+xml;base64,{base64.b64encode(svg).decode()})\n"
    sizes = DisplaySizes()
    sizes.add(
        xxh128(svg).hexdigest(),
        ImagePlacement(width_px=200, height_px=50, crop=SourceRect(top=0.5)),
    )

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown, sizes)

    with open(result.images[0].image_path, "rb") as f:
        assert f.read() == svg
    assert "?w=" not in result.markdown


@pytest.mark.asyncio
async def test_undecodable_image_bytes_drop_the_declared_size(tmp_path):
    """A PNG mime type on bytes Pillow cannot open: keep the image, drop the
    size that no longer describes it, and never fail the extraction."""
    junk = b"not really a png"
    markdown = f"![fig](data:image/png;base64,{base64.b64encode(junk).decode()})\n"
    sizes = DisplaySizes()
    sizes.add(
        xxh128(junk).hexdigest(),
        ImagePlacement(width_px=200, height_px=50, crop=SourceRect(left=0.25)),
    )

    with _uploads_patch(tmp_path):
        result = await extract_data_uri_images(markdown, sizes)

    with open(result.images[0].image_path, "rb") as f:
        assert f.read() == junk
    assert "?w=" not in result.markdown
