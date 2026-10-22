"""The comment export of a Word 97 binary main file — requires LibreOffice.

The .doc is made at test time from a .docx (fixtures stay out of binary form),
ingested the way the app ingests one, then exported with its data layer
stubbed. Each comment has to land on the paragraph its issue's lines point at.
"""

import asyncio
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
from docx_editor import Document as EditorDocument

from lib.models.issue import Issue
from lib.models.issue_edit import IssueEdit, IssueEditStatus
from lib.services.converters.docx_preprocessor import docx_preprocessor
from lib.services.docx.manipulator import DocxManipulatorType
from lib.services.docx.service import docx_manipulator_service, generate_docx
from lib.services.files.conversion import convert_file_document_to_markdown
from lib.services.files.document import FileDocument
from lib.workflows.models import SeverityEnum, WorkflowRunType
from tests.unit.services.docx.tracked_changes.support import display_fields

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
    profile = (workdir / "lo-profile").as_uri()  # private: tests run in parallel
    command = [_SOFFICE, "--headless", f"-env:UserInstallation={profile}"]
    command += ["--convert-to", "doc"]
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


def _edit(line: int, original: str, replacement: str) -> IssueEdit:
    return IssueEdit(
        id=uuid.uuid4(),
        issue_id=uuid.uuid4(),
        position=0,
        original_text=original,
        replacement_text=replacement,
        start_line=line,
        end_line=line,
        rationale="more precise",
        status=IssueEditStatus.PROPOSED,
        **display_fields(original, replacement, original),
    )


def _issue_on(markdown: str, text: str, edit: tuple[str, str]) -> Issue:
    line = next(i for i, ln in enumerate(markdown.split("\n"), 1) if text in ln)
    now = datetime.now(UTC)
    issue = Issue(
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
    issue.edit_rows = [_edit(line, *edit)]
    return issue


def _revisions(docx_path: str, workspace: Path) -> list[tuple[str, str]]:
    doc = EditorDocument.open(docx_path, author="Reader", workspace_dir=str(workspace))
    try:
        return [(r.type, r.text) for r in doc.list_revisions()]
    finally:
        doc.close()


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
    issue = _issue_on(main_file.markdown, "Bananas", ("tropical", "humid"))
    artifacts = MagicMock()
    artifacts.get_main_file = AsyncMock(return_value=main_file)
    project = SimpleNamespace(current_revision=1, group_by_severity=True)

    with (
        patch(f"{_SERVICE}.get_project_by_id", AsyncMock(return_value=project)),
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
    # python-docx leaves the tracked insertion out of the paragraph's text.
    assert _commented_paragraphs(output_path) == ["Bananas need a  climate."]
    # The tracked change is written into the converted document too.
    revisions = _revisions(output_path, tmp_path / "read-ws")
    assert sorted(revisions) == [("deletion", "tropical"), ("insertion", "humid")]
    # The converted copy is gone, and the upload is the only file left there.
    assert [p.name for p in uploads.iterdir()] == [Path(main_file.file_path).name]


@pytest.mark.asyncio
async def test_concurrent_conversions_all_succeed(tmp_path):
    # Each soffice run gets its own profile: on a shared one, a run started
    # while another holds it exits 0 without writing its output.
    source = _word_97_doc(tmp_path)
    copies = []
    for i in range(4):
        (tmp_path / f"run{i}").mkdir()
        copies.append(shutil.copyfile(source, tmp_path / f"run{i}" / "main.doc"))

    converted = await asyncio.gather(
        *(docx_preprocessor.convert_doc_to_docx(str(c)) for c in copies)
    )

    assert all(Path(p).read_bytes().startswith(b"PK") for p in converted)
