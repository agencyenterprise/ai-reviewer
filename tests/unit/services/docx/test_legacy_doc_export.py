"""Which main files the export reads through LibreOffice, and where it does."""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from lib.services.docx.legacy_doc import needs_libreoffice, readable_docx
from lib.services.files.document import FileDocument

MODULE = "lib.services.docx.legacy_doc"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOC_MIME = "application/msword"
OLE_HEADER = bytes.fromhex("d0cf11e0a1b11ae1") + b"\0" * 504
ZIP_HEADER = b"PK\x03\x04" + b"\0" * 26


def _main_file(path: Path, content: bytes, file_type: str) -> FileDocument:
    path.write_bytes(content)
    return FileDocument(
        file_id=str(uuid.uuid4()),
        file_path=str(path),
        file_name=path.name,
        file_type=file_type,
        markdown="",
        markdown_token_count=0,
    )


class TestNeedsLibreoffice:
    def test_a_word_2007_file_is_read_as_is(self, tmp_path):
        main = _main_file(tmp_path / "a.docx", ZIP_HEADER, DOCX_MIME)
        assert not needs_libreoffice(main)

    def test_a_word_2007_file_named_doc_is_read_as_is(self, tmp_path):
        # Ingestion copies these to .docx rather than converting them.
        main = _main_file(tmp_path / "a.doc", ZIP_HEADER, DOCX_MIME)
        assert not needs_libreoffice(main)

    def test_a_msword_doc_is_converted_as_ingestion_converted_it(self, tmp_path):
        # Even when the content is OOXML: ingestion went through LibreOffice
        # for it, so the issues' line numbers come from that conversion.
        main = _main_file(tmp_path / "a.doc", ZIP_HEADER, DOC_MIME)
        assert needs_libreoffice(main)

    def test_a_word_97_binary_is_converted_whatever_its_label(self, tmp_path):
        main = _main_file(tmp_path / "a.doc", OLE_HEADER, "application/octet-stream")
        assert needs_libreoffice(main)


class TestReadableDocx:
    @pytest.mark.asyncio
    async def test_a_word_2007_file_is_yielded_untouched(self, tmp_path):
        main = _main_file(tmp_path / "a.docx", ZIP_HEADER, DOCX_MIME)
        convert = AsyncMock()
        with patch(f"{MODULE}.docx_preprocessor.convert_doc_to_docx", convert):
            async with readable_docx(main) as path:
                assert path == main.file_path
        convert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_binary_is_converted_away_from_the_upload_and_cleaned_up(
        self, tmp_path
    ):
        uploads = tmp_path / "uploads"
        uploads.mkdir()
        main = _main_file(uploads / "c472.doc", OLE_HEADER, DOC_MIME)

        async def convert(source: str) -> str:
            converted = Path(source).with_suffix(".docx")
            converted.write_bytes(ZIP_HEADER)
            return str(converted)

        with patch(
            f"{MODULE}.docx_preprocessor.convert_doc_to_docx",
            AsyncMock(side_effect=convert),
        ):
            async with readable_docx(main) as path:
                assert Path(path).exists()
                assert Path(path).parent != uploads
                workdir = Path(path).parent

        assert not workdir.exists()
        assert sorted(p.name for p in uploads.iterdir()) == ["c472.doc"]
