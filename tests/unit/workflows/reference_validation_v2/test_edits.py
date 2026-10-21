from lib.agents.reference_validator_v2 import (
    BibliographyFieldValidationV2,
    BibliographyItemValidationV2,
    FieldCategoryV2,
    FieldProblemTypeV2,
    ReferenceValidationFinalResultV2,
)
from lib.workflows.reference_validation_v2.edits import (
    applies_full_correction,
    build_reference_edits,
)

REFERENCE = (
    'Patel, Dylan, Daniel Nishball, and Jeremie Elliahou Ontiveros, "AI Data '
    'center Energy Dilemma," SemiAnalysis, March 13, 2024.'
)
AUTHORS = "Patel, Dylan, Daniel Nishball, and Jeremie Elliahou Ontiveros"
LINES = ["# References", "", REFERENCE]


def _field(
    category: FieldCategoryV2, problem: FieldProblemTypeV2, current: str = ""
) -> BibliographyFieldValidationV2:
    return BibliographyFieldValidationV2(
        category=category,
        current_value=current,
        suggested_value=current,
        problem_type=problem,
    )


def _result(
    updated: str | None,
    *fields: BibliographyFieldValidationV2,
    final: ReferenceValidationFinalResultV2 = ReferenceValidationFinalResultV2.INCORRECT_FIELDS,
    url: str = "https://example.org/article",
) -> BibliographyItemValidationV2:
    return BibliographyItemValidationV2(
        original_reference=REFERENCE,
        final_result=final,
        bibliography_field_validations=list(fields),
        suggested_action="Fix it.",
        url=url,
        updated_reference=updated,
    )


AUTHOR_WRONG = _field(FieldCategoryV2.AUTHOR, FieldProblemTypeV2.INCORRECT, AUTHORS)
TITLE_RIGHT = _field(
    FieldCategoryV2.TITLE, FieldProblemTypeV2.CORRECT, "AI Data center Energy Dilemma"
)


def test_a_misspelled_name_becomes_one_small_replacement():
    result = _result(REFERENCE.replace("Elliahou", "Eliahou"), AUTHOR_WRONG)

    edits = build_reference_edits(result, REFERENCE, LINES, 3, 3)

    assert [(e.original_text, e.replacement_text, e.start_line) for e in edits] == [
        ("Elliahou", "Eliahou", 3)
    ]


def test_changes_to_a_field_marked_correct_are_dropped():
    updated = REFERENCE.replace("Elliahou", "Eliahou").replace(
        "Data center", "Datacenter"
    )
    result = _result(updated, AUTHOR_WRONG, TITLE_RIGHT)

    edits = build_reference_edits(result, REFERENCE, LINES, 3, 3)

    assert [e.replacement_text for e in edits] == ["Eliahou"]


def test_a_quote_found_twice_on_the_line_is_widened_until_it_is_unique():
    reference = "Smith, Jon, and Jon Doe, Jon's Book, 2020."
    field = _field(
        FieldCategoryV2.AUTHOR, FieldProblemTypeV2.INCORRECT, "Smith, Jon, and Jon Doe"
    )
    result = _result("Smith, Jon, and Jan Doe, Jon's Book, 2020.", field)

    edits = build_reference_edits(result, reference, [reference], 1, 1)

    assert [(e.original_text, e.replacement_text) for e in edits] == [
        ("and Jon Doe,", "and Jan Doe,")
    ]


def test_no_edit_when_the_text_is_not_on_the_reference_line():
    result = _result(REFERENCE.replace("Elliahou", "Eliahou"), AUTHOR_WRONG)

    assert build_reference_edits(result, REFERENCE, ["Something else"], 1, 1) == []


def test_no_edit_for_a_reference_that_was_not_found():
    result = _result(REFERENCE.replace("Elliahou", "Eliahou"), AUTHOR_WRONG, url="")

    assert build_reference_edits(result, REFERENCE, LINES, 3, 3) == []


def test_co_authors_inserted_into_an_incorrect_author_list_are_proposed():
    result = _result(
        REFERENCE.replace("Daniel Nishball,", "Daniel Nishball, Ana Lee,"),
        AUTHOR_WRONG,
    )

    edits = build_reference_edits(result, REFERENCE, LINES, 3, 3)

    assert [(e.original_text, e.replacement_text) for e in edits] == [
        ("Nishball,", "Nishball, Ana Lee,")
    ]


def test_one_change_across_two_incorrect_fields_is_proposed():
    reference = "Doe, Jane. A Study. arXiv preprint arXiv:2401.00001, 2024."
    result = _result(
        "Doe, Jane. A Study. ACL, 2024. arXiv:2401.13919.",
        _field(
            FieldCategoryV2.PUBLISHER, FieldProblemTypeV2.INCORRECT, "arXiv preprint"
        ),
        _field(
            FieldCategoryV2.IDENTIFIER, FieldProblemTypeV2.INCORRECT, "arXiv:2401.00001"
        ),
    )

    edits = build_reference_edits(result, reference, [reference], 1, 1)

    assert edits and edits[0].original_text.startswith("arXiv preprint")


def test_no_edit_for_missing_fields_only():
    missing = _field(FieldCategoryV2.PUBLISHER, FieldProblemTypeV2.MISSING)
    result = _result(
        REFERENCE.replace("SemiAnalysis,", "SemiAnalysis, Substack,"),
        missing,
        final=ReferenceValidationFinalResultV2.MISSING_FIELDS,
    )

    assert build_reference_edits(result, REFERENCE, LINES, 3, 3) == []


def test_no_edit_when_the_correction_rewrites_most_of_the_reference():
    field = _field(FieldCategoryV2.AUTHOR, FieldProblemTypeV2.INCORRECT, REFERENCE)
    result = _result(
        "Furrer, Daniel, Marc van Zee, and Nathan Scales, arXiv, 2020.", field
    )

    assert build_reference_edits(result, REFERENCE, LINES, 3, 3) == []


def test_edits_that_carry_the_whole_correction_are_recognised():
    corrected = REFERENCE.replace("Elliahou", "Eliahou")
    edits = build_reference_edits(
        _result(corrected, AUTHOR_WRONG), REFERENCE, LINES, 3, 3
    )

    assert applies_full_correction(REFERENCE, corrected, edits)


def test_edits_that_leave_part_of_the_correction_out_are_not_complete():
    corrected = REFERENCE.replace("Elliahou", "Eliahou").replace("2024", "2023")
    edits = build_reference_edits(
        _result(corrected, AUTHOR_WRONG), REFERENCE, LINES, 3, 3
    )

    assert edits
    assert not applies_full_correction(REFERENCE, corrected, edits)


def test_edits_widened_for_uniqueness_do_not_overlap():
    # "Ann," appears twice, so its edit widens to "Lee, Ann, Doe,"; the deleted
    # "and" takes "Doe," with it. Two edits sharing "Doe," conflict in the
    # export and one is not applied, yet the suggested action is left out.
    reference = "Lee, Ann, Doe, and Bo, Ann, Book, 2020."
    updated = "Lee, Ana, Doe, Bo, Ann, Book, 2020."
    field = _field(
        FieldCategoryV2.AUTHOR,
        FieldProblemTypeV2.INCORRECT,
        "Lee, Ann, Doe, and Bo, Ann",
    )
    result = _result(updated, field)

    edits = build_reference_edits(result, reference, ["# R", "", reference], 3, 3)

    words = [set(e.original_text.split()) for e in edits]
    assert all(not (a & b) for i, a in enumerate(words) for b in words[i + 1 :])
    assert applies_full_correction(reference, updated, edits)


def test_a_restyle_in_a_correct_field_is_dropped_even_when_its_word_is_in_an_incorrect_one():
    reference = "Smith and Jones, War and Peace, 2020."
    author = _field(
        FieldCategoryV2.AUTHOR, FieldProblemTypeV2.INCORRECT, "Smith and Jones"
    )
    title = _field(FieldCategoryV2.TITLE, FieldProblemTypeV2.CORRECT, "War and Peace")
    result = _result("Smyth and Jones, War & Peace, 2020.", author, title)

    edits = build_reference_edits(result, reference, [reference], 1, 1)

    assert [(e.original_text, e.replacement_text) for e in edits] == [
        ("Smith", "Smyth")
    ]


def test_an_author_field_restated_in_another_order_still_holds_its_fix():
    restated = _field(
        FieldCategoryV2.AUTHOR,
        FieldProblemTypeV2.INCORRECT,
        "Dylan Patel, Daniel Nishball, and Jeremie Elliahou Ontiveros",
    )
    result = _result(REFERENCE.replace("Elliahou", "Eliahou"), restated)

    edits = build_reference_edits(result, REFERENCE, LINES, 3, 3)

    assert [e.replacement_text for e in edits] == ["Eliahou"]


def test_a_missing_field_carried_in_by_an_incorrect_one_is_not_proposed():
    reference = "Doe, Jane. A Study. WrongVenue."
    venue = _field(
        FieldCategoryV2.PUBLISHER, FieldProblemTypeV2.INCORRECT, "WrongVenue"
    )
    year = _field(FieldCategoryV2.YEAR, FieldProblemTypeV2.MISSING, "")
    year.suggested_value = "2024"
    result = _result("Doe, Jane. A Study. CorrectVenue. 2024.", venue, year)

    assert build_reference_edits(result, reference, [reference], 1, 1) == []


def test_two_corrections_whose_quotes_would_share_a_word_become_one_edit():
    reference = "Doe, Jon and Jon Smith. A Study. 2020."
    authors = _field(
        FieldCategoryV2.AUTHOR, FieldProblemTypeV2.INCORRECT, "Doe, Jon and Jon Smith"
    )
    updated = "Doe, Jan and Jan Smith. A Study. 2020."
    result = _result(updated, authors)

    edits = build_reference_edits(result, reference, [reference], 1, 1)

    assert len(edits) == 1
    assert applies_full_correction(reference, updated, edits)


def test_a_restyle_of_a_correct_title_sharing_the_authors_surname_is_dropped():
    reference = "Brown, John. Brown Energy. Example Press, 2020."
    author = _field(FieldCategoryV2.AUTHOR, FieldProblemTypeV2.INCORRECT, "Brown, John")
    title = _field(FieldCategoryV2.TITLE, FieldProblemTypeV2.CORRECT, "Brown Energy")
    result = _result("Brown, Joan. BROWN Energy. Example Press, 2020.", author, title)

    edits = build_reference_edits(result, reference, [reference], 1, 1)

    assert [(e.original_text, e.replacement_text) for e in edits] == [
        ("John.", "Joan.")
    ]


def test_a_field_restated_in_another_order_is_not_placed_across_a_correct_field():
    reference = "Brown, John. Brown Energy. Example Press, 2020."
    author = _field(FieldCategoryV2.AUTHOR, FieldProblemTypeV2.INCORRECT, "John Brown")
    title = _field(FieldCategoryV2.TITLE, FieldProblemTypeV2.CORRECT, "Brown Energy")
    result = _result("Brown, Joan. BROWN Energy. Example Press, 2020.", author, title)

    edits = build_reference_edits(result, reference, [reference], 1, 1)

    assert [(e.original_text, e.replacement_text) for e in edits] == [
        ("John.", "Joan.")
    ]


def test_a_missing_value_of_several_words_is_caught_before_the_run_is_split():
    reference = "Doe, Jane, and Smith. A Study of Energy Policy, 2020."
    author = _field(
        FieldCategoryV2.AUTHOR, FieldProblemTypeV2.INCORRECT, "Doe, Jane, and Smith"
    )
    publisher = _field(FieldCategoryV2.PUBLISHER, FieldProblemTypeV2.MISSING, "")
    publisher.suggested_value = "RAND Corporation"
    result = _result(
        "Jones, Ann. RAND Corporation. A Study of Energy Policy, 2020.",
        author,
        publisher,
    )

    assert build_reference_edits(result, reference, [reference], 1, 1) == []
