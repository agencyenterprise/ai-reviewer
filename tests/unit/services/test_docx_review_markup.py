"""Reading reviewer comments and tracked changes out of a DOCX."""

import zipfile
from pathlib import Path

import pytest
from docx_editor import Document as EditorDocument

from lib.services.converters.base import convert_to_markdown
from lib.services.docx.review_markup import read_docx_review_markup
from lib.services.docx.review_markup_markdown import (
    comments_markdown,
    tracked_changes_markdown,
)
from tests.unit.services.lean_docx import new_document

_FIRST = "The survey reached 400 households across three districts."
_SECOND = "Response rates were highest in the northern district."


def _plain_docx(tmp_path: Path) -> Path:
    document = new_document()
    document.add_paragraph(_FIRST)
    document.add_paragraph(_SECOND)
    path = tmp_path / "draft.docx"
    document.save(str(path))
    return path


@pytest.fixture
def marked_up_docx(tmp_path: Path) -> Path:
    path = _plain_docx(tmp_path)
    doc = EditorDocument.open(
        path, author="Dr. Reviewer", workspace_dir=str(tmp_path / "ws")
    )
    try:
        comment_id = doc.add_comment("400 households", "How were these sampled?")
        doc.reply_to_comment(comment_id, "Stratified by district; see the methods.")
        doc.add_comment("northern district", "Say why.")
        second = doc.list_paragraphs_structured(limit=None)[1]
        doc.replace("highest", "lowest", paragraph=second.ref)
        doc.save()
    finally:
        doc.close()
    return path


def test_a_plain_document_has_no_markup(tmp_path: Path) -> None:
    markup = read_docx_review_markup(str(_plain_docx(tmp_path)))

    assert markup.comments == []
    assert markup.tracked_changes == []
    assert comments_markdown("draft.docx", markup) is None
    assert tracked_changes_markdown("draft.docx", markup) is None


def test_each_comment_keeps_the_text_it_is_attached_to(marked_up_docx: Path) -> None:
    markup = read_docx_review_markup(str(marked_up_docx))

    assert [c.text for c in markup.comments] == ["How were these sampled?", "Say why."]
    first, second = markup.comments
    assert first.anchor == "400 households"
    assert first.context == _FIRST
    assert first.author == "Dr. Reviewer"
    assert second.anchor == "northern district"


def test_replies_sit_under_the_comment_they_answer(marked_up_docx: Path) -> None:
    markup = read_docx_review_markup(str(marked_up_docx))

    assert [r.text for r in markup.comments[0].replies] == [
        "Stratified by district; see the methods."
    ]
    assert markup.comments[1].replies == []


def test_a_deletion_followed_by_an_insertion_reads_as_one_replacement(
    marked_up_docx: Path,
) -> None:
    markup = read_docx_review_markup(str(marked_up_docx))

    [change] = markup.tracked_changes
    assert change.kind == "replacement"
    assert (change.deleted, change.inserted) == ("highest", "lowest")
    assert change.author == "Dr. Reviewer"
    assert change.context == "Response rates were lowest in the northern district."


def test_the_markdown_names_the_document_and_quotes_each_item(
    marked_up_docx: Path,
) -> None:
    markup = read_docx_review_markup(str(marked_up_docx))

    comments = comments_markdown("draft.docx", markup)
    changes = tracked_changes_markdown("draft.docx", markup)

    assert comments is not None and changes is not None
    assert comments.startswith("# Comments in draft.docx")
    assert 'Attached to: "400 households"' in comments
    assert "> Stratified by district; see the methods." in comments
    assert 'Deleted: "highest"' in changes and 'Inserted: "lowest"' in changes


@pytest.mark.asyncio
async def test_the_converted_text_shows_the_revised_wording(
    marked_up_docx: Path,
) -> None:
    # The tracked-changes file tells the agent the converted text has the
    # insertions in place and the deletions removed; this keeps that true.
    markdown = await convert_to_markdown(str(marked_up_docx), converter="markitdown")

    assert "lowest" in markdown
    assert "highest" not in markdown


_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
_W15 = "http://schemas.microsoft.com/office/word/2012/wordml"


def _package(tmp_path: Path, body: str, comments: str = "", extended: str = "") -> Path:
    """A minimal DOCX from raw parts, for markup python-docx cannot write."""
    path = tmp_path / "raw.docx"
    with zipfile.ZipFile(path, "w") as package:
        package.writestr(
            "word/document.xml",
            f'<w:document xmlns:w="{_W}"><w:body>{body}</w:body></w:document>',
        )
        if comments:
            package.writestr(
                "word/comments.xml",
                f'<w:comments xmlns:w="{_W}" xmlns:w14="{_W14}">{comments}</w:comments>',
            )
        if extended:
            package.writestr(
                "word/commentsExtended.xml",
                f'<w15:commentsEx xmlns:w15="{_W15}">{extended}</w15:commentsEx>',
            )
    return path


def _comment(comment_id: int, para_id: str, text: str) -> str:
    return (
        f'<w:comment w:id="{comment_id}" w:author="Rev">'
        f'<w:p w14:paraId="{para_id}"><w:r><w:t>{text}</w:t></w:r></w:p></w:comment>'
    )


def test_a_reply_to_a_reply_stays_in_the_thread(tmp_path: Path) -> None:
    body = (
        '<w:p><w:commentRangeStart w:id="0"/><w:r><w:t>claim</w:t></w:r>'
        '<w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>'
    )
    comments = (
        _comment(0, "A0", "Root")
        + _comment(1, "A1", "First")
        + _comment(2, "A2", "Second")
    )
    # Chained the way LibreOffice writes them: each reply names the one before.
    extended = (
        '<w15:commentEx w15:paraId="A0"/>'
        '<w15:commentEx w15:paraId="A1" w15:paraIdParent="A0"/>'
        '<w15:commentEx w15:paraId="A2" w15:paraIdParent="A1"/>'
    )

    markup = read_docx_review_markup(str(_package(tmp_path, body, comments, extended)))

    [thread] = markup.comments
    assert [r.text for r in thread.replies] == ["First", "Second"]


def test_a_comment_on_deleted_text_is_anchored_to_it(tmp_path: Path) -> None:
    body = (
        '<w:p><w:r><w:t>Kept. </w:t></w:r><w:commentRangeStart w:id="0"/>'
        '<w:del w:id="9" w:author="Rev"><w:r><w:delText>struck words</w:delText></w:r></w:del>'
        '<w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>'
    )

    markup = read_docx_review_markup(
        str(_package(tmp_path, body, _comment(0, "A0", "Why cut this?")))
    )

    [comment] = markup.comments
    assert (comment.anchor, comment.anchor_deleted) == ("struck words", True)
    rendered = comments_markdown("raw.docx", markup)
    assert (
        rendered is not None and 'Attached to deleted text: "struck words"' in rendered
    )


def test_comments_follow_the_text_not_the_order_they_were_made(tmp_path: Path) -> None:
    def commented(comment_id: int, text: str) -> str:
        return (
            f'<w:p><w:commentRangeStart w:id="{comment_id}"/><w:r><w:t>{text}</w:t></w:r>'
            f'<w:commentRangeEnd w:id="{comment_id}"/>'
            f'<w:r><w:commentReference w:id="{comment_id}"/></w:r></w:p>'
        )

    # Comment 1 was made after comment 0 but sits above it; comment 2 is
    # anchored nowhere in the body.
    body = commented(1, "opening") + commented(0, "closing")
    comments = (
        _comment(0, "A0", "Second")
        + _comment(1, "A1", "First")
        + _comment(2, "A2", "Loose")
    )

    markup = read_docx_review_markup(str(_package(tmp_path, body, comments)))

    assert [c.text for c in markup.comments] == ["First", "Second", "Loose"]


def test_a_comment_keeps_its_line_breaks_and_tabs(tmp_path: Path) -> None:
    body = (
        '<w:p><w:commentRangeStart w:id="0"/><w:r><w:t>claim</w:t></w:r>'
        '<w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>'
    )
    comment = (
        '<w:comment w:id="0" w:author="Rev"><w:p w14:paraId="A0"><w:r>'
        "<w:t>Define X</w:t><w:br/><w:t>Give a citation</w:t><w:tab/><w:t>(p. 4)</w:t>"
        "</w:r></w:p></w:comment>"
    )

    [parsed] = read_docx_review_markup(str(_package(tmp_path, body, comment))).comments

    assert parsed.text == "Define X\nGive a citation\t(p. 4)"


def test_moved_away_text_reads_as_deleted(tmp_path: Path) -> None:
    body = (
        '<w:p><w:r><w:t>Kept. </w:t></w:r><w:commentRangeStart w:id="0"/>'
        '<w:moveFrom w:id="9" w:author="Rev"><w:r><w:t>moved words</w:t></w:r></w:moveFrom>'
        '<w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>'
    )

    markup = read_docx_review_markup(
        str(_package(tmp_path, body, _comment(0, "A0", "Why move this?")))
    )

    [comment] = markup.comments
    assert (comment.anchor, comment.anchor_deleted) == ("moved words", True)
    assert comment.context == "Kept."
    [change] = markup.tracked_changes
    assert (change.kind, change.deleted, change.context) == (
        "deletion",
        "moved words",
        "Kept.",
    )
