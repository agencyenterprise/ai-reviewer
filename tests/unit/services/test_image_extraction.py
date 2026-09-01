"""Unit tests for `lib.services.image_extraction`.

The invariant that matters most is line preservation: extraction rewrites each
image src in place, and issue anchors, `#L` links and the DOCX comment export
all assume the stored markdown's line numbers never move.
"""

import base64
import os
from unittest.mock import patch

import pytest

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
    from lib.services.docx.image_display_sizes import DisplaySizes

    sizes = DisplaySizes()
    content_hash = __import__("xxhash").xxh128(PNG_BYTES).hexdigest()
    sizes.add(content_hash, 150, 48)
    sizes.add(content_hash, 75, 24)
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
    from lib.services.docx.image_display_sizes import DisplaySizes

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
