"""Render a DOCX's reviewer markup as markdown an agent can read.

One file for the comments and one for the tracked changes, each written to
stand on its own: it names the document it belongs to and says how to find
each item again in that document's converted text.
"""

from typing import List, Optional

from lib.services.docx.review_markup import (
    DocxComment,
    DocxReviewMarkup,
    DocxTrackedChange,
)

# Long paragraphs are cut around this length; the anchor is what locates the
# item, the context only confirms it.
_CONTEXT_LIMIT = 600


def _quote(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines()) or ">"


def _clip(text: str) -> str:
    return text if len(text) <= _CONTEXT_LIMIT else text[:_CONTEXT_LIMIT].rstrip() + " …"


def _byline(author: str, date: Optional[str]) -> str:
    return f"{author}, {date}" if date else author


def _comment_block(number: int, comment: DocxComment) -> List[str]:
    status = " (resolved)" if comment.resolved else ""
    lines = [f"## Comment {number}: {_byline(comment.author, comment.date)}{status}", ""]
    if comment.anchor_deleted:
        lines += [f'Attached to deleted text: "{comment.anchor}"', ""]
    elif comment.anchor:
        lines += [f'Attached to: "{comment.anchor}"', ""]
    else:
        lines += ["Attached to: a single point in the text (no span selected)", ""]
    if comment.context:
        lines += [f'In the paragraph: "{_clip(comment.context)}"', ""]
    lines += ["Comment:", "", _quote(comment.text), ""]
    for reply in comment.replies:
        lines += [f"Reply from {_byline(reply.author, reply.date)}:", "", _quote(reply.text), ""]
    return lines


def comments_markdown(file_name: str, markup: DocxReviewMarkup) -> Optional[str]:
    """The document's comment threads, or None when it has none."""
    if not markup.comments:
        return None
    authors = sorted({c.author for c in markup.comments})
    lines = [
        f"# Comments in {file_name}",
        "",
        f"{len(markup.comments)} comment thread(s) by {', '.join(authors)}, in document order. "
        "Each gives the exact text it is attached to and the paragraph it sits in, "
        "so it can be found in the document's converted text.",
        "",
    ]
    for number, comment in enumerate(markup.comments, start=1):
        lines += _comment_block(number, comment)
    return "\n".join(lines).rstrip() + "\n"


def _change_block(number: int, change: DocxTrackedChange) -> List[str]:
    lines = [f"## Change {number}: {change.kind}, {_byline(change.author, change.date)}", ""]
    if change.deleted:
        lines += [f'Deleted: "{change.deleted.strip()}"', ""]
    if change.inserted:
        lines += [f'Inserted: "{change.inserted.strip()}"', ""]
    if change.context:
        lines += [f'In the paragraph, as revised: "{_clip(change.context)}"', ""]
    return lines


def visible_changes(markup: DocxReviewMarkup) -> List[DocxTrackedChange]:
    """The tracked changes that touch text, leaving out whitespace-only ones."""
    return [c for c in markup.tracked_changes if c.inserted.strip() or c.deleted.strip()]


def tracked_changes_markdown(file_name: str, markup: DocxReviewMarkup) -> Optional[str]:
    """The document's tracked insertions and deletions, or None when it has none."""
    changes = visible_changes(markup)
    if not changes:
        return None
    authors = sorted({c.author for c in changes})
    lines = [
        f"# Tracked changes in {file_name}",
        "",
        f"{len(changes)} tracked change(s) by {', '.join(authors)}, in document order. "
        "None of them has been accepted or rejected. The document's converted text "
        "shows each paragraph with the insertions in place and the deletions removed.",
        "",
    ]
    for number, change in enumerate(changes, start=1):
        lines += _change_block(number, change)
    return "\n".join(lines).rstrip() + "\n"
