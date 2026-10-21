"""The wording of a reference validation issue.

An author should see at a glance what is wrong with a reference, so the title
names the fields at fault and the description says what each one should be.
The issue carries no long description: the field-by-field breakdown, the source
and the validator's reasoning are on the assessment's results page.
"""

from lib.agents.reference_validator_v2 import (
    BibliographyFieldValidationV2,
    BibliographyItemValidationV2,
    FieldProblemTypeV2,
    ReferenceValidationFinalResultV2,
)

# Long field values (an author list of thirty names) are cut in the
# description; the assessment's results page shows them in full.
_VALUE_LIMIT = 120

_NOT_FOUND = (
    "This work could not be found online. It may be fabricated, or cited "
    "with details that are too far from the original to match it."
)


def _with(
    result: BibliographyItemValidationV2, problem: FieldProblemTypeV2
) -> list[BibliographyFieldValidationV2]:
    return [
        field
        for field in result.bibliography_field_validations
        if field.problem_type == problem
    ]


def _flagged(
    result: BibliographyItemValidationV2,
) -> list[BibliographyFieldValidationV2]:
    return [
        field
        for field in result.bibliography_field_validations
        if field.problem_type != FieldProblemTypeV2.CORRECT
    ]


def _not_found(result: BibliographyItemValidationV2) -> bool:
    return (
        result.final_result == ReferenceValidationFinalResultV2.INCORRECT_FIELDS
        and not result.url.strip()
    )


def _names(fields: list[BibliographyFieldValidationV2]) -> str:
    names = [field.category.value for field in fields]
    if len(names) <= 1:
        return "".join(names)
    return f"{', '.join(names[:-1])} and {names[-1]}"


def issue_title(result: BibliographyItemValidationV2) -> str:
    """A title naming the fields at fault, such as "Incorrect author and year"."""
    if result.final_result == ReferenceValidationFinalResultV2.CORRECT:
        return "Valid reference"
    if _not_found(result):
        return "Reference not found online"
    incorrect = _with(result, FieldProblemTypeV2.INCORRECT)
    missing = _with(result, FieldProblemTypeV2.MISSING)
    parts = []
    if incorrect:
        parts.append(f"incorrect {_names(incorrect)}")
    if missing:
        parts.append(f"missing {_names(missing)}")
    if not parts:
        return "Reference needs checking"
    title = "; ".join(parts)
    return title[0].upper() + title[1:]


def _clip(value: str) -> str:
    value = " ".join(value.split())
    return value if len(value) <= _VALUE_LIMIT else f"{value[: _VALUE_LIMIT - 1]}…"


def _field_sentence(field: BibliographyFieldValidationV2) -> str:
    name = field.category.value.capitalize()
    if field.problem_type == FieldProblemTypeV2.MISSING:
        return f"{name} is missing; the source gives “{_clip(field.suggested_value)}”."
    cited = _clip(field.current_value) or "nothing"
    return f"{name} is cited as “{cited}”; the source gives “{_clip(field.suggested_value)}”."


def issue_description(result: BibliographyItemValidationV2) -> str:
    """One or two sentences on what is wrong, the validator's own when it gave them."""
    if result.final_result == ReferenceValidationFinalResultV2.CORRECT:
        return "Author, title, publisher, year and identifier match the source."
    if result.summary.strip():
        return result.summary.strip()
    if _not_found(result):
        return _NOT_FOUND
    return " ".join(_field_sentence(field) for field in _flagged(result))
