"""Whether a quote will be found in the document, checked before anything is offered.

The add-in places each comment and edit by its quote: it must occur in exactly one
paragraph (``frontend/lib/addin/handoff-plan.ts``). A quote that is missing or repeated
is only discovered once the person chooses Apply, which is too late to fix it. The chat
agent has the same document as markdown, so the check can be made when the suggestion
is made, and the agent can correct its own quote.

The markdown is turned back into paragraph texts first: headings, paired emphasis,
links, escapes and table pipes are syntax the document does not contain. Each table
cell, and each paragraph within a cell, is its own paragraph in Word. The rules follow
what markitdown produces from a .docx, which is how the agent's copy is made.

Matching is the add-in's, so the two agree: ``normalize`` here and in
``handoff-plan.ts`` must stay the same.
"""

import re
from typing import Literal

Placement = Literal["found", "not_found", "ambiguous"]

_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})
# Hyphens, en and em dashes, minus signs: Word and the model disagree on these often.
_DASHES = re.compile(r"[‐‑‒–—―−]")
_SPACE = re.compile(r"\s+")

_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
_LIST = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_QUOTE_BLOCK = re.compile(r"^\s*>\s?")
_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|>~])")
_HELD = re.compile("\x00(\\d+)\x00")
# Emphasis is markup only where its markers pair up around text: a lone `*` or `_` in
# prose (`2*3`, `file_name`) is the document's own.
_PAIRED = [
    re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*"),
    re.compile(r"__(?=\S)(.+?)(?<=\S)__"),
    re.compile(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])"),
    re.compile(r"(?<![\w_])_(?=\S)(.+?)(?<=\S)_(?![\w_])"),
    re.compile(r"~~(?=\S)(.+?)(?<=\S)~~"),
    re.compile(r"`([^`]+)`"),
]
_TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_BLANK_LINE = re.compile(r"\n\s*\n")
_CELL_SEPARATOR = re.compile(r"(?<!\\)\|")
# markitdown collapses runs of spaces in text, except between two paragraphs of one
# table cell, which it joins with two.
_CELL_PARAGRAPHS = re.compile(r" {2,}")


def normalize(text: str) -> str:
    """The text as quotes are compared: quotes, dashes and runs of space evened out."""

    return _SPACE.sub(" ", _DASHES.sub("-", text.translate(_QUOTES))).strip()


def _plain(text: str) -> str:
    """Markdown back to the text Word holds: syntax removed, escapes undone."""

    text = _LINK.sub(r"\1", _QUOTE_BLOCK.sub("", _LIST.sub("", _HEADING.sub("", text))))
    # Escaped characters are the document's own: set them aside while emphasis goes.
    held: list[str] = []

    def hold(match: re.Match[str]) -> str:
        held.append(match.group(1))
        return f"\x00{len(held) - 1}\x00"

    text = _ESCAPE.sub(hold, text)
    for pattern in _PAIRED:
        text = pattern.sub(r"\1", text)
    return _HELD.sub(lambda match: held[int(match.group(1))], text)


def _starts_paragraph(line: str) -> bool:
    return bool(_HEADING.match(line) or _LIST.match(line) or _QUOTE_BLOCK.match(line))


def _table_paragraphs(lines: list[str]) -> list[str]:
    """A table's cells, each paragraph of a cell on its own."""

    texts: list[str] = []
    for line in lines:
        if _TABLE_RULE.match(line):
            continue
        for cell in _CELL_SEPARATOR.split(line.strip().strip("|")):
            texts.extend(_CELL_PARAGRAPHS.split(cell.strip()))
    return texts


def _prose_paragraphs(lines: list[str]) -> list[str]:
    """A block of prose: lines run on (a soft line break) until a list item or heading."""

    texts: list[str] = []
    for line in lines:
        if texts and not _starts_paragraph(line):
            texts[-1] = f"{texts[-1]} {line}"
        else:
            texts.append(line)
    return texts


def paragraph_texts(markdown: str) -> list[str]:
    """The document's paragraphs as plain text, as the add-in will read them.

    Paragraphs are separated by blank lines, and a single line break inside one is a
    soft break Word reads as space. List items and headings start their own paragraph.
    A block is a table only when it has a `---` rule; a `|` in prose is text.
    """

    paragraphs: list[str] = []
    for block in _BLANK_LINE.split(markdown):
        lines = [line for line in block.splitlines() if line.strip()]
        is_table = any(_TABLE_RULE.match(line) for line in lines)
        texts = _table_paragraphs(lines) if is_table else _prose_paragraphs(lines)
        paragraphs.extend(text for raw in texts if (text := normalize(_plain(raw))))
    return paragraphs


def place(quote: str, paragraphs: list[str]) -> Placement:
    """Whether ``quote`` occurs exactly once, within one paragraph, as the add-in requires.

    Twice in one paragraph is as ambiguous as once in each of two: the add-in would
    change the first, whichever was meant. The quote is compared as plain text, which is what the agent is told to send and
    what the add-in looks for: markdown in it is not stripped, since it would not be
    found in Word either.
    """

    wanted = normalize(quote)
    if not wanted:
        return "not_found"
    hits = sum(occurrences(text, wanted) for text in paragraphs)
    if hits == 0:
        return "not_found"
    return "found" if hits == 1 else "ambiguous"


def occurrences(text: str, wanted: str) -> int:
    """How many times ``wanted`` starts in ``text``, overlapping ones included.

    ``str.count`` skips overlaps: it finds ``ana`` once in ``banana``, where it starts
    twice.
    """

    count, at = 0, text.find(wanted)
    while at != -1:
        count += 1
        at = text.find(wanted, at + 1)
    return count


def overlapping(quotes: list[str], paragraphs: list[str]) -> list[str]:
    """The quotes whose words an earlier quote in the list covers too.

    The add-in finds every edit before writing any, so an edit over words another edit
    replaces would land on that edit's text: it refuses the later one
    (``handoff-plan.ts``). Quotes not found once are left to ``place``.
    """

    taken: list[tuple[int, int, int]] = []
    clashing: list[str] = []
    for quote in quotes:
        wanted = normalize(quote)
        where = [(i, t.find(wanted)) for i, t in enumerate(paragraphs) if wanted in t]
        if not wanted or len(where) != 1:
            continue
        paragraph, start = where[0]
        end = start + len(wanted)
        if any(p == paragraph and s < end and start < e for p, s, e in taken):
            clashing.append(quote)
        else:
            taken.append((paragraph, start, end))
    return clashing
