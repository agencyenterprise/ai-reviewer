from lib.agents.reference_validator_v2 import (
    BibliographyFieldValidationV2,
    BibliographyItemValidationV2,
    FieldCategoryV2,
    FieldProblemTypeV2,
    ReferenceValidationFinalResultV2,
)
from lib.workflows.reference_validation_v2.issue_text import (
    issue_description,
    issue_title,
)


def _field(
    category: FieldCategoryV2, problem: FieldProblemTypeV2, current: str, suggested: str
) -> BibliographyFieldValidationV2:
    return BibliographyFieldValidationV2(
        category=category,
        current_value=current,
        suggested_value=suggested,
        problem_type=problem,
    )


YEAR_WRONG = _field(FieldCategoryV2.YEAR, FieldProblemTypeV2.INCORRECT, "2019", "2021")
AUTHOR_WRONG = _field(
    FieldCategoryV2.AUTHOR, FieldProblemTypeV2.INCORRECT, "Smyth", "Smith"
)
PUBLISHER_MISSING = _field(
    FieldCategoryV2.PUBLISHER, FieldProblemTypeV2.MISSING, "", "RAND"
)
TITLE_RIGHT = _field(
    FieldCategoryV2.TITLE, FieldProblemTypeV2.CORRECT, "A Study", "A study"
)


def _result(
    *fields: BibliographyFieldValidationV2,
    final: ReferenceValidationFinalResultV2 = ReferenceValidationFinalResultV2.INCORRECT_FIELDS,
    url: str = "https://example.org",
    summary: str = "",
) -> BibliographyItemValidationV2:
    return BibliographyItemValidationV2(
        original_reference="Smyth, A Study, 2019.",
        final_result=final,
        bibliography_field_validations=list(fields),
        suggested_action="Fix it.",
        url=url,
        summary=summary,
        reasoning="Searched the title.",
        updated_reference="Smith, A Study, RAND, 2021.",
    )


def test_title_names_the_incorrect_and_missing_fields():
    result = _result(AUTHOR_WRONG, YEAR_WRONG, PUBLISHER_MISSING, TITLE_RIGHT)

    assert issue_title(result) == "Incorrect author and year; missing publisher"


def test_title_for_a_reference_that_was_not_found():
    assert issue_title(_result(AUTHOR_WRONG, url="")) == "Reference not found online"


def test_description_prefers_the_validators_summary():
    result = _result(YEAR_WRONG, summary="The report came out in 2021, not 2019.")

    assert issue_description(result) == "The report came out in 2021, not 2019."


def test_description_falls_back_to_the_fields_at_fault():
    result = _result(YEAR_WRONG, TITLE_RIGHT)

    assert issue_description(result) == (
        "Year is cited as “2019”; the source gives “2021”."
    )
