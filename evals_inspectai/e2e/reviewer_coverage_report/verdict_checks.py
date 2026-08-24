"""Checks specific to the reviewer coverage report's verdict bookkeeping.

The coverage report is the one review-assistant output with an arithmetic core.
Its Part 1 carries a table counting every reviewer point across four verdict
categories, with the point IDs listed alongside each count, and Part 2 records a
verdict under each quoted point. That gives three things a rule can check
exactly, without judging whether any individual verdict is *right*:

- the four categories are all present, including the ones that scored zero;
- the table accounts for every point exactly once;
- Part 1 states the recommendation the QAM needs.

Whether each verdict is correct is a judgement, and is graded by the rubric.
"""

import re

from evals_inspectai.common.html_report import (
    HtmlReport,
    PointId,
    expand_point_ids,
    find_point_ids,
    normalize,
    tables,
)

# The scale the skill defines. Order matters: the longer labels are matched
# first so "addressed" does not swallow "partially addressed".
VERDICTS = (
    "declined with rationale",
    "partially addressed",
    "not addressed",
    "addressed",
)

# The QAM's decision, in either direction. Deliberately does not match a bare
# "another pass": the skill requires a "What needs another pass" heading, so
# that phrasing is always present and matching it would make this vacuous.
_RECOMMENDATION = re.compile(
    # Either a sign-off, or a verb of returning followed within a few words by
    # what is being returned for. Reports phrase the second one freely:
    # "return for another pass", "return for a targeted second pass",
    # "returning the draft for one more focused pass", "send it back for
    # revision". The window is wide because the qualifiers stack up; it still
    # needs a verb of returning, which is what keeps the required heading
    # "What needs another pass" from matching on its own.
    r"sign[\s-]*off"
    r"|(?:return|returned|returns|returning|send|sends|sending|sent)\b"
    r"(?:\W+\w+){0,8}?\W+(?:pass|revision|round|rework)",
    re.IGNORECASE,
)

# The count a cell states, which precedes the ids it lists.
_LEADING_COUNT = re.compile(r"\s*(\d{1,3})")


def _verdict_of(cell: str) -> str | None:
    """Which verdict category a table cell names, if any."""
    text = normalize(cell)
    for verdict in VERDICTS:
        if verdict in text:
            return verdict
    return None


def _transpose(table: list[list[str]]) -> list[list[str]]:
    width = max(len(row) for row in table)
    padded = [row + [""] * (width - len(row)) for row in table]
    return [list(col) for col in zip(*padded)]


def find_verdict_table(report: HtmlReport) -> list[list[str]] | None:
    """The summary table, oriented so each row is one verdict category.

    Chosen by content rather than position, since a report may carry other
    tables. Both orientations occur: usually the verdicts run down the first
    column, but some reports put the verdicts across the header and one row per
    reviewer. A transposed table is turned the right way up rather than
    rejected, which is what "no verdict table found" used to mean.
    """
    candidates = tables(report.html)
    for table in candidates:
        labelled = {_verdict_of(row[0]) for row in table if row and _verdict_of(row[0])}
        if len(labelled) >= 3:
            return table
    for table in candidates:
        if not table:
            continue
        flipped = _transpose(table)
        labelled = {
            _verdict_of(row[0]) for row in flipped if row and _verdict_of(row[0])
        }
        if len(labelled) >= 3:
            return flipped
    return None


def check_verdict_table(report: HtmlReport) -> tuple[bool, str]:
    """The table names all four categories and accounts for every point once.

    The counts are not compared against a per-scenario expectation: which
    verdict a point deserves is a judgement the rubric grades. What is checked
    is that the bookkeeping holds together, which is what makes the table
    usable at all.
    """
    table = find_verdict_table(report)
    if table is None:
        return False, "no verdict table found"

    rows = {
        verdict: row
        for row in table
        if row and (verdict := _verdict_of(row[0])) is not None
    }
    missing = [v for v in VERDICTS if v not in rows]
    if missing:
        return False, f"table omits {missing}"

    problems: list[str] = []

    # Every id the table assigns, per category, with ranges expanded.
    assigned: dict[str, set[PointId]] = {}
    for verdict, row in rows.items():
        # The last cell is the total when the table breaks counts down per
        # reviewer; scanning the whole row and taking the union avoids
        # depending on the column layout.
        assigned[verdict] = set(expand_point_ids(" ".join(row[1:])))

    # A point belongs to exactly one category.
    seen: dict[PointId, str] = {}
    for verdict, ids in assigned.items():
        for point in sorted(ids):
            if point in seen and seen[point] != verdict:
                problems.append(
                    f"{point} counted under both {seen[point]} and {verdict}"
                )
            seen[point] = verdict

    # The table covers every point the report labels in Part 2. A point split
    # into sub-points is covered by them: when A3 becomes A3.1, A3.2 and A3.3,
    # the table counts the three and not the parent, which is correct.
    counted = set(seen)
    parents_covered = {
        PointId(point.split(".")[0]) for point in counted if "." in point
    }
    labelled = set(find_point_ids(report.raw_text))
    uncounted = sorted(labelled - counted - parents_covered)
    if uncounted:
        problems.append(
            f"{len(uncounted)} point(s) missing from the table: {uncounted[:6]}"
        )

    # The stated counts match the ids. Reports lay this out three ways: a cell
    # carrying both ("8, A1-A8" or "9 A1, A2, ..."), or a bare count cell with
    # the ids in a column of their own. Pairing within a cell whenever the cell
    # has both handles the first two and the per-reviewer breakdown, where a
    # bare "0" is one reviewer's count and not the row's total.
    for verdict, row in rows.items():
        cells = row[1:]
        paired: list[tuple[int, int, str]] = []
        bare: list[int] = []
        for cell in cells:
            match = _LEADING_COUNT.match(cell)
            if not match:
                continue
            listed = len(set(expand_point_ids(cell)))
            if listed:
                paired.append((int(match.group(1)), listed, cell))
            elif cell.strip().isdigit():
                bare.append(int(match.group(1)))

        if paired:
            for stated, listed, cell in paired:
                if stated != listed:
                    problems.append(
                        f"{verdict}: cell states {stated} but lists "
                        f"{listed} id(s) ({cell[:40]!r})"
                    )
        elif bare and max(bare) != len(assigned[verdict]):
            problems.append(
                f"{verdict}: row states {max(bare)} but lists "
                f"{len(assigned[verdict])} id(s)"
            )

    summary = ", ".join(f"{v}={len(assigned[v])}" for v in VERDICTS)
    return (
        not problems,
        f"{summary}; {len(seen)} points counted"
        + ("; " + "; ".join(problems) if problems else ""),
    )


def check_verdict_vocabulary(report: HtmlReport) -> tuple[bool, str]:
    """Part 2 uses the four defined verdicts and does not invent others.

    A report that collapses the scale to addressed/not addressed loses the
    distinction the skill exists to preserve: a decline with a stated reason is
    settled, and only `not addressed` should read as a gap.

    The summary table's own labels are discounted first. `find_verdict_table`
    only recognises a table when at least three of its rows name a verdict, so
    counting across the whole report meant any report with a usable table
    cleared the bar automatically and this check could never fail. What it asks
    now is that the scale is used where it does the work, under the points in
    Part 2, rather than only declared in the header of a table.
    """
    table = find_verdict_table(report)
    table_text = normalize(" ".join(" ".join(row) for row in table)) if table else ""

    counts = {v: report.text.count(v) - table_text.count(v) for v in VERDICTS}
    # "addressed" is a substring of the other three labels, so discount those.
    counts["addressed"] -= (
        counts["partially addressed"]
        + counts["not addressed"]
        + (report.text.count("declined") - table_text.count("declined"))
    )
    used = [v for v, n in counts.items() if n > 0]
    detail = ", ".join(f"{v}={max(n, 0)}" for v, n in counts.items())
    if len(used) < 2:
        return (
            False,
            f"outside the summary table the verdict scale is barely used: {detail}",
        )
    return True, f"outside the summary table: {detail}"


def check_recommendation(report: HtmlReport) -> tuple[bool, str]:
    """Part 1 states the QAM's decision explicitly.

    The report exists to answer one question: sign off, or send the revision
    back. Leaving the reader to infer it from the counts fails the output's
    stated purpose.
    """
    head = report.text[: int(0.4 * len(report.text))] or report.text
    match = _RECOMMENDATION.search(head)
    if not match:
        return False, "no explicit sign-off or return-for-another-pass recommendation"
    return True, f"recommendation stated ({match.group(0)!r})"
