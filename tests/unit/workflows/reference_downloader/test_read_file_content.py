"""read_file_content reads downloaded PDFs with pypdfium and reports unreadable files."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from lib.models.file import File
from lib.workflows.reference_downloader.tools import read_file_content as rfc

FILE_ID = "6f1c2a7e-0b8d-4c55-9a3e-2d4f6b8c0e11"
TITLE = "Doctrine for the Armed Forces"


def _pdf_with_empty_inline_image_filter(text: str) -> bytes:
    """A one-page PDF whose content stream holds an inline image with `/F []`.

    pdfminer indexes the empty filter list and raises IndexError on it, which
    is what failed Joint Publication 1 in the reference downloader eval.
    """
    stream = (
        f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET\n"
        "q 10 0 0 10 72 600 cm BI /W 1 /H 1 /CS /G /BPC 8 /F [] ID \x00 EI Q\n"
    ).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R"
        b" /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


def _file(path: Path, file_type: str) -> MagicMock:
    file = MagicMock(spec=File)
    file.file_path = str(path)
    file.file_type = file_type
    return file


@pytest.mark.asyncio
async def test_reads_a_pdf_that_pdfminer_cannot_parse(tmp_path: Path) -> None:
    path = tmp_path / "jp1.pdf"
    path.write_bytes(_pdf_with_empty_inline_image_filter(TITLE))

    with patch.object(
        rfc, "get_file_by_id", AsyncMock(return_value=_file(path, "application/pdf"))
    ):
        content = await rfc._read_file_content_async(FILE_ID)

    assert content is not None
    assert TITLE in content


@pytest.mark.asyncio
async def test_an_unreadable_file_returns_the_reason(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not a pdf")

    with patch.object(
        rfc, "get_file_by_id", AsyncMock(return_value=_file(path, "application/pdf"))
    ):
        content = await rfc._read_file_content_async(FILE_ID)

    assert content is not None
    assert content.startswith(f"Could not read file {FILE_ID}")


@pytest.mark.asyncio
async def test_an_unknown_file_id_returns_the_reason() -> None:
    missing = HTTPException(status_code=404, detail="File not found")

    with patch.object(rfc, "get_file_by_id", AsyncMock(side_effect=missing)):
        content = await rfc._read_file_content_async(FILE_ID)

    assert content is not None
    assert content.startswith(f"Could not read file {FILE_ID}")
