"""Reading the workflow's delivery: labels out of titles, rows out of tables.

Both are text parsing against output the agent writes freely, so both have been
wrong in ways that scored a correct report down: an anchor matched inside a
larger number, and a report's inventory table was confused with a bigger table
copied from the document.
"""

import re

from evals_inspectai.common.simple_deep_agent_types import IssueItem
from evals_inspectai.e2e.results_extraction.contract import REPRODUCIBILITY_LABELS

_LABEL = re.compile(r"\(([^()]+)\)\s*$")

# Markdown table rows, with the outer pipes optional: GFM allows
# `Title | Location | Label` and a report written that way used to score zero
# rows. A row has to contain at least one pipe to count.
_TABLE_ROW = re.compile(r"^\s*\|?[^|\n]*\|.*$")
_TABLE_DIVIDER = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|[\s:|-]*$")

# The inventory table is identified by what the skill asks it to carry, not by
# being the biggest table in the report: a document's own results table, copied
# into the report, is often larger and would mask a truncated inventory.
_INVENTORY_HEADER = re.compile(r"reproducib", re.I)


def label_of(issue: IssueItem) -> str | None:
    """The reproducibility label in a result issue's title, lowercased."""
    match = _LABEL.search(issue.title.strip())
    if match is None:
        return None
    label = match.group(1).strip().lower()
    return label if label in REPRODUCIBILITY_LABELS else None


def table_row_count(report: str) -> tuple[int, str]:
    """Data rows in the report's inventory table, and how it was identified.

    Walks each markdown table, keeping the one whose header names a
    reproducibility column. Falls back to the widest table only when no header
    qualifies, so a report that labels its inventory is scored on that table and
    one that does not is still scored on something.
    """
    lines = report.splitlines()
    tables: list[tuple[bool, int]] = []  # (header names reproducibility, rows)
    index = 0
    while index < len(lines):
        if _TABLE_DIVIDER.match(lines[index]) and index > 0:
            titled = bool(_INVENTORY_HEADER.search(lines[index - 1]))
            rows = 0
            index += 1
            while index < len(lines) and _TABLE_ROW.match(lines[index]):
                rows += 1
                index += 1
            tables.append((titled, rows))
            continue
        index += 1

    inventories = [rows for titled, rows in tables if titled]
    if inventories:
        return max(inventories), "inventory table (header names reproducibility)"
    if tables:
        return max(rows for _, rows in tables), "widest table (no header named reproducibility)"
    return 0, "no markdown table found"

