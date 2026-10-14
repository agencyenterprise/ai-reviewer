"""Cheap pre-check for whether a document could have an Abbreviations section.

The section extractor reads the whole document in one model call to find a
section titled "Abbreviations", "Acronyms" or "Glossary". When none of those
words appears, there is nothing to find, and on a long document the call is
the most expensive one in the workflow. This check lets the node skip it.
Plain text processing; no model is involved.

It matches the words anywhere rather than only on title-like lines: converted
PDFs glue titles onto running headers ("...Frontier ModelsAbbreviations") and
space out table-of-contents leaders, so a stricter test misses real sections.
"""

import re

_SECTION_WORD_RE = re.compile(r"abbreviation|acronym|glossary", re.IGNORECASE)


def find_candidate_lines(markdown: str) -> list[int]:
    """1-indexed lines containing "abbreviation", "acronym" or "glossary" (any case)."""
    return [
        number
        for number, line in enumerate(markdown.split("\n"), start=1)
        if _SECTION_WORD_RE.search(line)
    ]
