"""Tracked-change edits for a reference the validator could correct with confidence.

The validator returns a corrected copy of the reference. The difference between
the two, word by word, gives the edits: each run of changed words becomes one
small replacement ("Elliahou" -> "Eliahou") rather than the whole reference
being struck and retyped, so an author reviewing the redline sees only what is
wrong.

An edit is proposed only where the fix is not in doubt:

- the reference was found and has at least one field marked incorrect, with a
  source URL behind it (a field that is only missing would need an insertion
  whose place in the citation style is a guess, so it stays a suggested action);
- the corrected reference keeps most of the original's words, since a rewrite
  of most of a citation is a judgment call for the author, not a redline;
- every word a change touches lies inside a field marked incorrect (for an
  insertion, the word it is inserted next to, as when co-authors are added to
  an author list). The validator sometimes restyles a field it marked correct
  (a title's capitalization, a URL's form); those changes are dropped;
- the quoted text is found once on the reference's own line of the document.
"""

import difflib
from collections.abc import Sequence

from pydantic import BaseModel

from lib.agents.reference_validator_v2 import (
    BibliographyFieldValidationV2,
    BibliographyItemValidationV2,
    FieldProblemTypeV2,
    ReferenceValidationFinalResultV2,
)
from lib.workflows.models import ProposedEdit
from lib.workflows.simple_deep_agent.edit_anchoring import find_quote_lines
from lib.workflows.simple_deep_agent.issue_reporting import (
    ProposedEditInput,
    resolve_edit,
)

# The share of the original's words the corrected reference must keep. Below
# it the correction is a rewrite (a whole author list and venue swapped).
_MIN_WORDS_KEPT = 0.6

# More changed runs than this is also a rewrite, however short each one is.
_MAX_EDITS = 4

_EDGE_PUNCTUATION = "\"'“”‘’,.;:()[]"


class _WordChange(BaseModel):
    """One run of changed words, as word indices into the original."""

    start: int
    end: int
    replacement: list[str]


def build_reference_edits(
    result: BibliographyItemValidationV2,
    reference_text: str,
    lines: Sequence[str],
    start_line: int,
    end_line: int,
) -> list[ProposedEdit]:
    """The edits that turn the cited reference into the validator's correction."""
    incorrect = _incorrect_fields(result)
    if not _is_confident(result, incorrect):
        return []

    original = reference_text.split()
    corrected = (result.updated_reference or "").split()
    matcher = difflib.SequenceMatcher(a=original, b=corrected, autojunk=False)
    kept = sum(block.size for block in matcher.get_matching_blocks())
    if not original or kept / len(original) < _MIN_WORDS_KEPT:
        return []

    changes = [
        _WordChange(start=i1, end=i2, replacement=corrected[j1:j2])
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]
    if len(changes) > _MAX_EDITS:
        return []

    edits: list[ProposedEdit] = []
    for change in changes:
        fields = _fields_holding(_touched_words(change, original), incorrect)
        if not fields:
            continue
        edit = _locate(change, original, lines, start_line, end_line)
        if edit is not None:
            edits.append(edit)
    return edits


def _incorrect_fields(
    result: BibliographyItemValidationV2,
) -> list[BibliographyFieldValidationV2]:
    return [
        field
        for field in result.bibliography_field_validations
        if field.problem_type == FieldProblemTypeV2.INCORRECT
    ]


def _is_confident(
    result: BibliographyItemValidationV2,
    incorrect: list[BibliographyFieldValidationV2],
) -> bool:
    return (
        result.final_result == ReferenceValidationFinalResultV2.INCORRECT_FIELDS
        and bool(incorrect)
        and bool(result.url.strip())
        and bool((result.updated_reference or "").strip())
    )


def _normalized(word: str) -> str:
    return word.strip(_EDGE_PUNCTUATION).lower()


def _touched_words(change: _WordChange, original: list[str]) -> list[str]:
    """The original's words a change replaces, or for an insertion its neighbour."""
    if change.start < change.end:
        return original[change.start : change.end]
    neighbour = change.start - 1 if change.start > 0 else change.start
    return original[neighbour : neighbour + 1]


def _fields_holding(
    words: list[str], fields: list[BibliographyFieldValidationV2]
) -> list[BibliographyFieldValidationV2]:
    """The incorrect fields holding the touched words, or none if any word is outside them."""
    held: list[BibliographyFieldValidationV2] = []
    for word in filter(None, map(_normalized, words)):
        field = next(
            (f for f in fields if word in map(_normalized, f.current_value.split())),
            None,
        )
        if field is None:
            return []
        if field not in held:
            held.append(field)
    return held


def _locate(
    change: _WordChange,
    original: list[str],
    lines: Sequence[str],
    start_line: int,
    end_line: int,
) -> ProposedEdit | None:
    """Anchor one change on the reference's line, widening it until it is unique."""
    start, end = change.start, change.end
    if not change.replacement or start == end:
        # A deletion takes a neighbouring word with it, so the space before
        # the deleted words goes too; an insertion needs one to quote.
        start, end = (start - 1, end) if start > 0 else (start, end + 1)
    while True:
        quote = " ".join(original[start:end])
        if len(find_quote_lines(lines, start_line, end_line, quote)) == 1:
            break
        if start == 0 and end == len(original):
            return None
        start, end = max(0, start - 1), min(len(original), end + 1)

    replacement = " ".join(
        [
            *original[start : change.start],
            *change.replacement,
            *original[change.end : end],
        ]
    )
    outcome = resolve_edit(
        lines,
        ProposedEditInput(
            original_text=quote,
            replacement_text=replacement,
            # The issue's description already says what is wrong; a rationale
            # would repeat it under every edit.
            rationale="",
        ),
        "edit",
        start_line,
        end_line,
    )
    return outcome if isinstance(outcome, ProposedEdit) else None


def applies_full_correction(
    reference_text: str, updated_reference: str | None, edits: Sequence[ProposedEdit]
) -> bool:
    """Whether applying the edits to the reference gives the validator's correction.

    Then the edits say everything a suggested action would, so the issue can
    leave the action out.
    """
    if not edits or not updated_reference:
        return False
    text = " ".join(reference_text.split())
    for edit in edits:
        quote = " ".join(edit.original_text.split())
        if quote not in text:
            return False
        text = text.replace(quote, " ".join(edit.replacement_text.split()), 1)
    return text == " ".join(updated_reference.split())
