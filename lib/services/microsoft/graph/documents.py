"""A SharePoint document, loaded and read as text.

The backend holds a real .docx here rather than the Flat OPC an add-in sends, so
``docx-editor`` opens it directly and none of the adapter in
``lib/services/microsoft/word/word_package.py`` is involved. That is the one clear
simplification of loading documents server-side.

Read-only. Writing back is refused by SharePoint with 423 while anyone has the
document open, so it is not offered here at all.
"""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from docx_editor import Document
from pydantic import BaseModel, Field

from lib.services.microsoft.graph import client

logger = logging.getLogger(__name__)


class LoadedDocument(BaseModel):
    """What the agent needs to answer a question about a document."""

    name: str
    url: str
    paragraphs: list[str] = Field(
        description="Every paragraph in order, so positions can be referred to"
    )
    comments: list[tuple[str, str]] = Field(
        default_factory=list, description="(author, text), threads and replies alike"
    )
    last_modified: Optional[str] = None
    size_bytes: int = 0

    @property
    def text(self) -> str:
        return "\n".join(self.paragraphs)


def _read(path: Path, work: Path) -> tuple[list[str], list[tuple[str, str]]]:
    """Paragraphs and comments, via docx-editor on a real file."""

    doc = Document.open(path, author="Draft Detective", workspace_dir=str(work / "ws"))
    try:
        paragraphs = [info.text for info in doc.list_paragraphs_structured(limit=None)]
        comments: list[tuple[str, str]] = []
        for comment in doc.list_comments():
            comments.append((comment.author, comment.text))
            for reply in comment.replies:
                comments.append((reply.author, reply.text))
    finally:
        doc.close()
    return paragraphs, comments


async def load(url: str) -> LoadedDocument:
    """Load a document by its SharePoint URL.

    Raises ``client.DocumentNotAllowed`` when the URL is outside the configured
    sites, and ``client.GraphError`` when Graph will not serve it.
    """

    item = await client.resolve(url)
    payload = await client.download(item)
    logger.info(
        "loaded %s (%s bytes, modified %s)",
        item.get("name"),
        len(payload),
        item.get("lastModifiedDateTime"),
    )

    work = Path(tempfile.mkdtemp(prefix="dd-graph-"))
    try:
        path = work / "document.docx"
        path.write_bytes(payload)
        # docx-editor is synchronous and unzips into a workspace, so it does not
        # belong on the event loop.
        paragraphs, comments = await asyncio.to_thread(_read, path, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    return LoadedDocument(
        name=str(item.get("name") or "document.docx"),
        url=url,
        paragraphs=paragraphs,
        comments=comments,
        last_modified=item.get("lastModifiedDateTime"),
        size_bytes=len(payload),
    )
