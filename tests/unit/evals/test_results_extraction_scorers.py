"""Behaviour of the results_extraction scorer helpers.

Each test here corresponds to a way the scorer has misread a correct output, or
passed an incorrect one, in a recorded run:

- greedy assignment stranded a result that matched only one issue, reporting it
  missing and the issue that took its place as an invention;
- the table counter required outer pipes, so a GFM table written without them
  counted zero rows, and it took the widest table, so a copied data table could
  mask a truncated inventory;
- line ranges were checked for order but not against the document's length;
- augmenting the matching freely could demote a title hit to a body hit, raising
  the match count while attributing both classes to the wrong results.
"""

from evals_inspectai.common.simple_deep_agent_types import AgentCheckResult, IssueItem
from evals_inspectai.e2e.results_extraction.results_extraction_e2e import (
    _inventory_checks,
    _match_expected,
    _table_row_count,
)


def _issue(title: str, description: str = "", severity: str = "none") -> IssueItem:
    return IssueItem(
        title=title,
        description=description,
        severity=severity,
        start_line=1,
        end_line=2,
    )


class TestMatchExpected:
    def test_a_constrained_result_is_not_stranded(self):
        """The result matching one issue keeps it; the flexible one moves.

        `wide` matches both issues, `narrow` only the first. Taking pairs in
        order gave `wide` the first issue and left `narrow` unmatched, which read
        as a missing result plus an invented one. Both should match.
        """
        issues = [
            _issue("Result: alpha and beta (Fully Reproducible)"),
            _issue("Result: beta only (Fully Reproducible)"),
        ]
        expected = [
            {"id": "wide", "match": ["beta"], "class": "fully_reproducible", "importance": "central"},
            {"id": "narrow", "match": ["alpha"], "class": "fully_reproducible", "importance": "central"},
        ]
        matched = _match_expected(issues, expected)
        assert set(matched) == {"wide", "narrow"}
        assert matched["narrow"] == 0
        assert matched["wide"] == 1

    def test_a_title_hit_outranks_a_body_hit(self):
        """An anchor in the title binds before the same anchor in prose."""
        issues = [
            _issue("Result: something else (Not Reproducible)", "mentions Table 1 in passing"),
            _issue("Result: Table 1 summary (Not Reproducible)"),
        ]
        expected = [
            {"id": "tab1", "match": ["table 1"], "class": "not_reproducible", "importance": "central"},
        ]
        assert _match_expected(issues, expected) == {"tab1": 1}

    def test_a_title_match_is_never_demoted_to_a_body_match(self):
        """Raising the match count is not worth mis-attributing a class.

        The `alpha` issue mentions beta in its prose, and a second issue mentions
        alpha only in its prose. Augmenting freely would move `alpha` onto that
        second issue and hand its own titled issue to `beta` -- two matches
        instead of one, both pointing at the wrong result. `alpha` keeps its
        title hit and `beta` stays unmatched.
        """
        issues = [
            _issue("Result: alpha measurement (Not Reproducible)", "compared against beta"),
            _issue("Result: something unrelated (Not Reproducible)", "mentions alpha in passing"),
        ]
        expected = [
            {"id": "alpha", "match": ["alpha"], "class": "not_reproducible", "importance": "central"},
            {"id": "beta", "match": ["beta"], "class": "not_reproducible", "importance": "central"},
        ]
        matched = _match_expected(issues, expected)
        assert matched == {"alpha": 0}, matched

    def test_two_results_merged_into_one_issue_leaves_one_unmatched(self):
        """One-to-one is what makes merging visible."""
        issues = [_issue("Result: alpha and beta together (Not Reproducible)")]
        expected = [
            {"id": "a", "match": ["alpha"], "class": "not_reproducible", "importance": "central"},
            {"id": "b", "match": ["beta"], "class": "not_reproducible", "importance": "central"},
        ]
        assert len(_match_expected(issues, expected)) == 1


class TestTableRowCount:
    def test_outer_pipes_are_optional(self):
        report = "Title | Location | Reproducibility\n--- | --- | ---\nA | Fig 1 | Not Reproducible\nB | Tab 1 | Fully Reproducible\n"
        rows, _ = _table_row_count(report)
        assert rows == 2

    def test_the_inventory_table_wins_over_a_bigger_one(self):
        """A copied data table must not stand in for a truncated inventory."""
        report = (
            "## Data copied from the document\n\n"
            "| # | Value |\n|---|---|\n" + "".join(f"| {i} | {i * 2} |\n" for i in range(10))
            + "\n## Inventory\n\n"
            "| Title | Location | Reproducibility |\n|---|---|---|\n"
            "| A | Figure 1 | Not Reproducible |\n"
        )
        rows, how = _table_row_count(report)
        assert rows == 1, "should count the inventory table, not the 10-row data table"
        assert "reproducibility" in how

    def test_no_table_at_all(self):
        assert _table_row_count("just prose")[0] == 0


class TestLineRanges:
    def _checks(self, issue: IssueItem, document_lines: int):
        result = AgentCheckResult(
            issues=[issue],
            report_markdown="x" * 500
            + "\n\n| Title | Location | Reproducibility |\n|---|---|---|\n| A | B | Not Reproducible |\n",
        )
        meta = {
            "expected_results": [
                {"id": "a", "match": ["alpha"], "class": "not_reproducible", "importance": "central"}
            ]
        }
        return _inventory_checks(result, meta, document_lines)

    def test_a_range_past_the_end_of_the_document_fails(self):
        issue = _issue("Result: alpha (Not Reproducible)", severity="high")
        issue.start_line, issue.end_line = 900, 905
        ok, detail = self._checks(issue, document_lines=100)["line_ranges"]
        assert not ok
        assert "100 lines" in detail

    def test_a_range_inside_the_document_passes(self):
        issue = _issue("Result: alpha (Not Reproducible)", severity="high")
        issue.start_line, issue.end_line = 10, 12
        ok, _ = self._checks(issue, document_lines=100)["line_ranges"]
        assert ok

    def test_duplicate_titles_are_caught(self):
        duplicate = _issue("Result: alpha (Not Reproducible)", severity="high")
        result = AgentCheckResult(
            issues=[duplicate, duplicate.model_copy()],
            report_markdown="x" * 500,
        )
        meta = {"expected_results": [{"id": "a", "match": ["alpha"], "class": "not_reproducible", "importance": "central"}]}
        ok, detail = _inventory_checks(result, meta, 100)["no_duplicates"]
        assert not ok
        assert "2 times" in detail
