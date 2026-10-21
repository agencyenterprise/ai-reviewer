"""Give the export a .docx it can open when the main file is a Word 97 binary."""

import asyncio
import shutil
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from lib.services.converters.docx_preprocessor import docx_preprocessor
from lib.services.files.document import FileDocument

LEGACY_DOC_MIME = "application/msword"
# Every Word 97-2003 binary is an OLE compound file, and starts with this.
_OLE_SIGNATURE = bytes.fromhex("d0cf11e0a1b11ae1")


def _is_ole_file(file_path: str) -> bool:
    with open(file_path, "rb") as f:
        return f.read(len(_OLE_SIGNATURE)) == _OLE_SIGNATURE


def needs_libreoffice(main_file: FileDocument) -> bool:
    """Whether the file's markdown came from a LibreOffice conversion.

    Mirrors ingestion, which converts an ``application/msword`` ``.doc`` with
    LibreOffice before making markdown, so the export must read that same
    conversion for issue line numbers to land on the right paragraphs. A file
    that is an OLE binary whatever its label is converted too: python-docx
    cannot open one at all.
    """
    labelled_legacy = (
        main_file.file_type == LEGACY_DOC_MIME
        and Path(main_file.file_path).suffix.lower() == ".doc"
    )
    return labelled_legacy or _is_ole_file(main_file.file_path)


@asynccontextmanager
async def readable_docx(main_file: FileDocument) -> AsyncIterator[str]:
    """Yield a path python-docx can open for the main file.

    A Word 2007+ file is yielded as is. A Word 97 binary is converted with the
    same LibreOffice step ingestion uses, in a temporary directory removed on
    exit: the upload directory is left alone, so concurrent exports and
    ingestion never share or delete each other's converted copy.
    """
    if not needs_libreoffice(main_file):
        yield main_file.file_path
        return
    with tempfile.TemporaryDirectory(prefix="legacy-doc-") as workdir:
        source = Path(workdir) / f"{Path(main_file.file_path).stem}.doc"
        await asyncio.to_thread(shutil.copyfile, main_file.file_path, source)
        yield await docx_preprocessor.convert_doc_to_docx(str(source))
