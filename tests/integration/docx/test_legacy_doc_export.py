"""The comment export of a Word 97 binary main file — requires LibreOffice.

The .doc is made at test time from a .docx (fixtures stay out of binary form),
ingested the way the app ingests one, then exported with its data layer
stubbed. Each comment has to land on the paragraph its issue's lines point at.
"""

import shutil
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from docx import Document
from docx.oxml.ns import qn

from lib.models.issue import Issue
from lib.services.docx.manipulator import DocxManipulatorType
from lib.services.docx.service import docx_manipulator_service, generate_docx
from lib.services.files.conversion import convert_file_document_to_markdown
from lib.services.files.document import FileDocument
from lib.workflows.models import SeverityEnum, WorkflowRunType

_SOFFICE = shutil.which("soffice") or shutil.which("libreoffice")
_SERVICE = "lib.services.docx.service"
_OLE_SIGNATURE = bytes.fromhex("d0cf11e0a1b11ae1")
_PARAGRAPHS = [
    "Apples grow in temperate orchards.",
    "Bananas need a tropical climate.",
    "Cherries blossom early in spring.",
]

pytestmark = pytest.mark.skipif(_SOFFICE is None, reason="LibreOffice not installed")


def _word_97_doc(workdir: Path) -> Path:
    """A Word 97 binary holding `_PARAGRAPHS`, saved by LibreOffice."""
    source = workdir / "source.docx"
    doc = Document()
    for text in _PARAGRAPHS:
        doc.add_paragraph(text)
    doc.save(str(source))
    assert _SOFFICE is not None
    command = [_SOFFICE, "--headless", "--convert-to", "doc"]
    command += ["--outdir", str(workdir), str(source)]
    subprocess.run(command, check=True, capture_output=True, timeout=120)
    converted = workdir / "source.doc"
    assert converted.read_bytes().startswith(_OLE_SIGNATURE)
    return converted


async def _ingested(uploads: Path) -> FileDocument:
    """The main file as ingestion leaves it: the .doc, and markdown made from it."""
    upload = uploads / f"{uuid.uuid4().hex}.doc"
    shutil.copyfile(_word_97_doc(uploads.parent), upload)
    main_file = FileDocument(
        file_id="",  # no id: image extraction, the only DB step, is skipped
        file_path=str(upload),
        file_name="legacy.doc",
        file_type="application/msword",
        markdown="",
        markdown_token_count=0,
    )
    return await convert_file_document_to_markdown(main_file)


def _issue_on(markdown: str, text: str) -> Issue:
    line = next(i for i, ln in enumerate(markdown.split("\n"), 1) if text in ln)
    now = datetime.now(UTC)
    return Issue(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        workflow_run_id=uuid.uuid4(),
        issue_hash=uuid.uuid4().hex,
        title="Check this",
        description=f"About: {text}",
        severity=SeverityEnum.HIGH,
        workflow_type=WorkflowRunType.RECOMMENDATION_CHECK,
        start_line=line,
        end_line=line,
        created_at=now,
        updated_at=now,
    )


def _commented_paragraphs(docx_path: str) -> list[str]:
    return [
        p.text
        for p in Document(docx_path).paragraphs
        if p._p.findall(f".//{qn('w:commentRangeStart')}")
    ]


@pytest.mark.asyncio
async def test_a_word_97_main_file_exports_its_comments(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    main_file = await _ingested(uploads)
    issue = _issue_on(main_file.markdown, "Bananas")
    artifacts = MagicMock()
    artifacts.get_main_file = AsyncMock(return_value=main_file)
    project = SimpleNamespace(current_revision=1)

    with (
        patch(f"{_SERVICE}._get_project_by_id", AsyncMock(return_value=project)),
        patch(f"{_SERVICE}.FileArtifactsService", MagicMock(return_value=artifacts)),
        patch(f"{_SERVICE}.get_project_issues", AsyncMock(return_value=[issue])),
        patch.object(docx_manipulator_service, "get_output_dir", return_value=tmp_path),
    ):
        output_path, filename = await generate_docx(
            project_id=str(uuid.uuid4()),
            share_token=None,
            docx_type=DocxManipulatorType.COMMENTS,
            include_edits=True,
        )

    assert filename == "legacy_comments.docx"
    assert _commented_paragraphs(output_path) == [_PARAGRAPHS[1]]
    # The converted copy is gone, and the upload is the only file left there.
    assert [p.name for p in uploads.iterdir()] == [Path(main_file.file_path).name]
