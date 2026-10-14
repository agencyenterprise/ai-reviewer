"""Read a DOCX's reviewer markup: its comments and its tracked changes.

The markdown conversion keeps a document's text and drops everything a reviewer
layered on top of it: the comment threads in the margin and the insertions and
deletions they tracked. A reviewer who only marked up the draft leaves nothing
in that markdown, so this module reads the markup straight from the OOXML.

Each comment comes back with the text it is attached to and the paragraph
around it, so a reader can find it again in the converted document. Each
tracked change comes back with the paragraph it sits in, as revised. Reading
only: nothing here writes to the file.
"""

import zipfile
from collections.abc import Iterator
from typing import Literal

from lxml import etree
from pydantic import BaseModel, Field

from lib.services.docx.namespaces import W14, W15, W, qn, w

_CORE_DC = "http://purl.org/dc/elements/1.1/"
_CORE_CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
_CORE_TERMS = "http://purl.org/dc/terms/"
_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"

# Uploads are untrusted: no entity expansion and no network lookups.
_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)

_INSERTED = {w("ins"), w("moveTo")}
_DELETED = {w("del"), w("moveFrom")}
_COMMENT_MARKS = {w("commentRangeStart"), w("commentReference")}


class DocxComment(BaseModel):
    """One comment, with the text it is attached to."""

    id: str
    author: str
    date: str | None = None
    text: str
    anchor: str = Field(default="", description="The document text the comment covers")
    anchor_deleted: bool = Field(
        default=False,
        description="The comment covers only text a tracked change deletes, which is its anchor",
    )
    context: str = Field(default="", description="The paragraph the comment starts in")
    resolved: bool = False
    replies: list["DocxComment"] = Field(default_factory=list)


class DocxTrackedChange(BaseModel):
    """One tracked edit. A deletion directly followed by an insertion by the
    same author is reported as one replacement."""

    kind: Literal["insertion", "deletion", "replacement"]
    author: str
    date: str | None = None
    inserted: str = ""
    deleted: str = ""
    context: str = Field(default="", description="The paragraph, as revised")


class DocxProperties(BaseModel):
    """What the package says about who wrote and last saved the file."""

    author: str | None = None
    last_modified_by: str | None = None
    created: str | None = None
    modified: str | None = None


class DocxReviewMarkup(BaseModel):
    properties: DocxProperties = Field(default_factory=DocxProperties)
    comments: list[DocxComment] = Field(default_factory=list)
    tracked_changes: list[DocxTrackedChange] = Field(default_factory=list)


class _Segment(BaseModel):
    """A run of paragraph text, and the tracked change it belongs to, if any."""

    model_config = {"arbitrary_types_allowed": True}

    text: str
    change: etree._Element | None = None
    deleted: bool = False


def _read_part(package: zipfile.ZipFile, name: str) -> etree._Element | None:
    if name not in package.namelist():
        return None
    return etree.fromstring(package.read(name), _PARSER)


def _attr(element: etree._Element, name: str, namespace: str = W) -> str | None:
    return element.get(qn(name, namespace))


def _date(element: etree._Element) -> str | None:
    value = _attr(element, "date")
    return value[:10] if value else None


def _squash(text: str) -> str:
    return " ".join(text.split())


def _read_properties(package: zipfile.ZipFile) -> DocxProperties:
    core = _read_part(package, "docProps/core.xml")
    if core is None:
        return DocxProperties()

    def field(tag: str, namespace: str) -> str | None:
        node = core.find(qn(tag, namespace))
        return _squash(node.text) if node is not None and node.text else None

    return DocxProperties(
        author=field("creator", _CORE_DC),
        last_modified_by=field("lastModifiedBy", _CORE_CP),
        created=field("created", _CORE_TERMS),
        modified=field("modified", _CORE_TERMS),
    )


def _comment_text(comment: etree._Element) -> str:
    paragraphs = [
        "".join(t.text or "" for t in p.iter(w("t"))) for p in comment.iter(w("p"))
    ]
    return "\n".join(p.strip() for p in paragraphs if p.strip())


def _read_comments(package: zipfile.ZipFile) -> dict[str, DocxComment]:
    """Every comment by id, threaded: replies sit under the comment they answer."""
    root = _read_part(package, "word/comments.xml")
    if root is None:
        return {}

    comments: dict[str, DocxComment] = {}
    para_ids: dict[str, str] = {}
    for element in root.iter(w("comment")):
        comment_id = _attr(element, "id") or ""
        comments[comment_id] = DocxComment(
            id=comment_id,
            author=_attr(element, "author") or "Unknown",
            date=_date(element),
            text=_comment_text(element),
        )
        paragraphs = list(element.iter(w("p")))
        # Word threads replies by the id of the comment's last paragraph.
        if paragraphs and (para_id := paragraphs[-1].get(qn("paraId", W14))):
            para_ids[para_id] = comment_id

    parent_of: dict[str, str] = {}
    extended = _read_part(package, "word/commentsExtended.xml")
    for entry in extended.iter(qn("commentEx", W15)) if extended is not None else []:
        entry_id = para_ids.get(entry.get(qn("paraId", W15)) or "")
        if entry_id is None:
            continue
        comments[entry_id].resolved = entry.get(qn("done", W15)) == "1"
        parent_id = para_ids.get(entry.get(qn("paraIdParent", W15)) or "")
        if parent_id is not None and parent_id != entry_id:
            parent_of[entry_id] = parent_id

    # Word points every reply at the thread's first comment; other editors
    # chain each reply to the one before. Either way the reply belongs to the
    # thread's root, which is the only level the thread is rendered at.
    for reply_id in parent_of:
        root_id = _thread_root(reply_id, parent_of)
        if root_id != reply_id:
            comments[root_id].replies.append(comments[reply_id])
            comments[reply_id].id = f"reply:{reply_id}"
    return comments


def _thread_root(comment_id: str, parent_of: dict[str, str]) -> str:
    """The first comment of the thread ``comment_id`` is in, safe on a cycle."""
    seen = {comment_id}
    while (parent := parent_of.get(comment_id)) is not None and parent not in seen:
        seen.add(parent)
        comment_id = parent
    return comment_id


def _body_paragraphs(document: etree._Element) -> Iterator[etree._Element]:
    """Body paragraphs in reading order, skipping the fallback copies Word
    keeps of text boxes (the same text twice)."""
    for paragraph in document.iter(w("p")):
        if not any(a.tag == qn("Fallback", _MC) for a in paragraph.iterancestors()):
            yield paragraph


def _change_of(
    node: etree._Element, paragraph: etree._Element
) -> etree._Element | None:
    for ancestor in node.iterancestors():
        if ancestor is paragraph:
            return None
        if ancestor.tag in _INSERTED or ancestor.tag in _DELETED:
            return ancestor
    return None


def _belongs_to(node: etree._Element, paragraph: etree._Element) -> bool:
    """Whether ``node`` is the paragraph's own, not a paragraph nested in it.

    A text box sits inside the paragraph that anchors it, as paragraphs of its
    own (twice over, with Word's fallback copy). Those are read as paragraphs in
    their own right, so the anchoring paragraph must not read them again.
    """
    for ancestor in node.iterancestors():
        if ancestor.tag == w("p"):
            return ancestor is paragraph
    return False


def _segments(paragraph: etree._Element) -> Iterator[tuple[etree._Element, _Segment]]:
    """The paragraph's text pieces and comment markers, in document order."""
    for node in paragraph.iter():
        if node is paragraph or not _belongs_to(node, paragraph):
            continue
        if node.tag in (w("t"), w("delText")):
            change = _change_of(node, paragraph)
            deleted = node.tag == w("delText")
            yield node, _Segment(text=node.text or "", change=change, deleted=deleted)
        elif node.tag in (w("tab"), w("br")):
            yield node, _Segment(text=" ", change=_change_of(node, paragraph))
        else:
            yield node, _Segment(text="")


def read_docx_review_markup(docx_path: str) -> DocxReviewMarkup:
    """Read the comments and tracked changes out of a DOCX file."""
    with zipfile.ZipFile(docx_path) as package:
        properties = _read_properties(package)
        comments = _read_comments(package)
        document = _read_part(package, "word/document.xml")
    if document is None:
        return DocxReviewMarkup(properties=properties)

    walker = _MarkupWalker(comments)
    for paragraph in _body_paragraphs(document):
        walker.read_paragraph(paragraph)

    return DocxReviewMarkup(
        properties=properties,
        comments=_in_document_order(comments, walker.encountered),
        tracked_changes=walker.changes,
    )


def _in_document_order(
    comments: dict[str, DocxComment], encountered: list[str]
) -> list[DocxComment]:
    """Thread roots in the order their anchors appear in the body.

    A comment's id is the order it was created in, which is not where it sits:
    a later comment can be attached earlier in the text, and paragraphs move.
    A comment whose anchor is nowhere in the body follows, by id.
    """
    top_level = {cid: c for cid, c in comments.items() if not c.id.startswith("reply:")}
    anchored = [
        top_level[cid] for cid in dict.fromkeys(encountered) if cid in top_level
    ]
    seen = {c.id for c in anchored}
    orphans = sorted(
        (c for c in top_level.values() if c.id not in seen),
        key=lambda c: _sort_key(c.id),
    )
    return anchored + orphans


def _sort_key(comment_id: str) -> tuple[int, str]:
    return (int(comment_id), "") if comment_id.isdigit() else (1 << 30, comment_id)


class _MarkupWalker:
    """Walks body paragraphs once, filling comment anchors and collecting changes."""

    def __init__(self, comments: dict[str, DocxComment]) -> None:
        self._comments = comments
        self._open: dict[str, list[str]] = {}
        # What the comment covers that a tracked change deletes: the anchor to
        # fall back on when that is all it covers.
        self._open_deleted: dict[str, list[str]] = {}
        self.changes: list[DocxTrackedChange] = []
        # Comment ids as the body first marks them, which is document order.
        self.encountered: list[str] = []

    def read_paragraph(self, paragraph: etree._Element) -> None:
        pieces = list(_segments(paragraph))
        context = _squash("".join(s.text for _, s in pieces if not s.deleted))
        started: list[str] = []

        for node, segment in pieces:
            comment_id = _attr(node, "id")
            if node.tag in _COMMENT_MARKS and comment_id in self._comments:
                self.encountered.append(comment_id)
            if node.tag == w("commentRangeStart") and comment_id in self._comments:
                self._open[comment_id] = []
                self._open_deleted[comment_id] = []
                started.append(comment_id)
            elif node.tag == w("commentRangeEnd") and comment_id in self._open:
                self._close(comment_id)
            elif node.tag == w("commentReference") and comment_id in self._comments:
                if not self._comments[comment_id].context:
                    started.append(comment_id)
            elif segment.text:
                target = self._open_deleted if segment.deleted else self._open
                for anchor in target.values():
                    anchor.append(segment.text)

        for comment_id in started:
            if not self._comments[comment_id].context:
                self._comments[comment_id].context = context
        for anchor in self._open.values():
            anchor.append(" / ")
        self._collect_changes([s for _, s in pieces if s.text], context)

    def _close(self, comment_id: str) -> None:
        comment = self._comments[comment_id]
        live = _squash("".join(self._open.pop(comment_id)).strip(" /"))
        deleted = _squash("".join(self._open_deleted.pop(comment_id, [])))
        comment.anchor = live or deleted
        comment.anchor_deleted = not live and bool(deleted)

    def _collect_changes(self, segments: list[_Segment], context: str) -> None:
        grouped: list[tuple[etree._Element | None, str]] = []
        for segment in segments:
            if grouped and grouped[-1][0] is segment.change:
                grouped[-1] = (segment.change, grouped[-1][1] + segment.text)
            else:
                grouped.append((segment.change, segment.text))

        pending: DocxTrackedChange | None = None
        for change, text in grouped:
            if change is None:
                pending = None
                continue
            author = _attr(change, "author") or "Unknown"
            if change.tag in _DELETED:
                pending = DocxTrackedChange(
                    kind="deletion",
                    author=author,
                    date=_date(change),
                    deleted=text,
                    context=context,
                )
                self.changes.append(pending)
            elif pending is not None and pending.author == author:
                pending.kind = "replacement"
                pending.inserted = text
                pending = None
            else:
                self.changes.append(
                    DocxTrackedChange(
                        kind="insertion",
                        author=author,
                        date=_date(change),
                        inserted=text,
                        context=context,
                    )
                )
                pending = None
