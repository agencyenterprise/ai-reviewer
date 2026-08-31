"""E2E eval for the results_extraction (Reproducibility Check) workflow.

The workflow is a simple deep agent running the `reproducibility-check` skill:
it reports one issue per result it extracts -- reproducible ones as
informational `none` items, so the issue list is the document's full result
inventory -- and writes the summary, inventory table and per-result detail to
`report_markdown`.

Scoring is in two parts, and every check is its own metric rather than one
blended number, so a regression names itself in the results table:

- `inventory_checks`: ten deterministic rules. Six are about the shape of the
  delivery -- a substantive report, an inventory table covering every result,
  enough results found, a reproducibility label on every issue title, the
  severity split the skill mandates, and usable line ranges. Four compare the
  inventory against the dataset's ground truth: whether every expected result
  was found, whether each was given the right reproducibility class, whether
  anything was invented, and whether the severities of the non-reproducible
  results are ordered by how much the document rests on them.
- `rubric_criteria`: two judged criteria, each graded in its own call so a weak
  area cannot colour the rest -- whether each classification is grounded in
  what the document supplies, and the per-sample expectations from the dataset.

Anything the dataset can state as ground truth is checked deterministically
rather than judged. An earlier generic `inventory_complete` criterion, which
asked a grader whether an inventory was complete given only the document, graded
five *identical* 3-result inventories 0, 0.5, 1, 1, 0.5: without per-sample
ground truth the grader re-litigates the grouping on every call. Each dataset
record now carries its `expected_results`, so completeness, classification and
severity ordering are all decided by comparison instead.

Which of low/medium/high a non-reproducible result earns is the agent's
judgement of importance, so the deterministic pass deliberately checks only
that it is *some* real severity and leaves the level to the judged criterion.
"""

import re
from pathlib import Path
from typing import Any

import yaml
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import Model, get_model
from inspect_ai.scorer import Score, Scorer, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState
from inspect_ai.viewer import (
    SampleScoreView,
    SampleScoreViewSort,
    ScoreColorScale,
    TaskSamplesColumn,
    TaskSamplesSort,
    TaskSamplesView,
    ViewerConfig,
)
from pydantic import ValidationError

from evals_inspectai.common.api_solver import api_workflow_agent
from evals_inspectai.common.scorers import (
    REQUIREMENT_TEMPLATE,
    checks_to_score,
    criteria_for,
    failed_score,
    grade_criteria,
)
from evals_inspectai.common.simple_deep_agent_types import (
    AgentCheckResult,
    IssueItem,
    SimpleDeepAgentOutput,
)

# Grader for the judged criteria, pinned per suite rather than inherited, so
# changing this suite's judge does not silently re-grade any other.
GRADER_MODEL = "openai/gpt-5.4"

# Below this the report is a stub, whatever else it gets right. The skill asks
# for a summary paragraph, a table of every result and a section per result that
# is not fully reproducible, which does not fit in less.
MIN_REPORT_CHARS = 400

# The four reproducibility labels, as they appear in an issue title's trailing
# parenthesis: `Result: <title> (<label>)`.
REPRODUCIBILITY_LABELS = (
    "fully reproducible",
    "reproducible with web search",
    "reproducible with external uploads",
    "not reproducible",
)

# Anything reproducible -- even only with web search or external uploads -- is
# informational; only "not reproducible" carries a real severity.
NOT_REPRODUCIBLE = "not reproducible"
REAL_SEVERITIES = {"low", "medium", "high"}

# One key per deterministic rule.
INVENTORY_CHECKS = (
    "report",
    "inventory_table",
    "result_count",
    "labels",
    "severity_split",
    "line_ranges",
    "no_duplicates",
    "completeness",
    "class_accuracy",
    "no_extras",
    "severity_ordering",
)

# The judged criteria. One holds for every sample; `sample_expectations`
# carries the dataset's own per-sample rubric. The key set has to be identical
# across samples, because Inspect raises when a declared metric key is missing
# from any score.
RUBRIC_CRITERIA = (
    "classification_grounded",
    "sample_expectations",
)

SHARED_CRITERIA: dict[str, str] = {
    "classification_grounded": (
        "Each result's rationale is grounded in what the document supplies: it names the "
        "specific ingredients present or missing -- the data, parameters, equations, procedural "
        "steps -- and how a reader would obtain anything missing, rather than asserting the "
        "class or restating its definition. Where something is missing, it says what has to be "
        "supplied without inventing the values.\n\n"
        "Judge only the quality of that reasoning, not whether you would have picked the same "
        "class. The four classes are defined as follows, and a rationale consistent with any of "
        "them is grounded:\n"
        "- Fully Reproducible: the logic is explained and everything needed is in the document, "
        "appendices included.\n"
        "- Reproducible with Web Search: the logic is explained, and what is missing is "
        "individual published values a reader can look up from openly accessible sources.\n"
        "- Reproducible with External Uploads: the logic is explained, and what is missing is a "
        "bulk dataset open to any reader, which has to be downloaded.\n"
        "- Not Reproducible: the logic is not explained, or what is missing cannot be obtained "
        "at all -- confidential, proprietary, paid-access, withheld, or never recorded.\n\n"
        "None of the following is a deficiency and a rationale must not be marked down for "
        "declining to treat it as one: a figure or table not rendered in the text conversion; a "
        "plot of the document's own model, which is regenerated by running that model; no "
        "published code; values reported rounded; a reader having to fetch sources or re-run a "
        "long computation; or a stochastic result whose seed and generator are fixed."
    ),
}

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


def _record_to_sample(record: dict) -> Sample:
    """Build a sample from one dataset record.

    `expected_results` is the record's ground-truth inventory: one entry per
    result the document presents, each with the substrings that identify it, the
    reproducibility class it should be given, and how much the document rests on
    it. The count of the required entries is also the floor for `result_count`,
    so there is no separate expected-count field to drift out of sync.

    An entry with `"required": false` is a reading the document supports without
    demanding -- a number stated in a conclusion that could reasonably be folded
    into the figure it came from. Reporting one is not an invention and not a
    miss, so it counts for `no_extras` and `class_accuracy` but not for
    `completeness`. Every other extra still fails `no_extras`, which is what
    keeps over-splitting visible.

    `target_answer` becomes the `sample_expectations` criterion rather than a
    target string, so it is graded in its own call alongside the shared one.
    """
    return Sample(
        id=record["id"],
        input=record["input"],
        target=record.get("target_answer", ""),
        metadata={
            "expected_results": record.get("expected_results", []),
            "expects_no_results": bool(record.get("expects_no_results")),
            "rubric": {"sample_expectations": record.get("target_answer", "")},
        },
    )


def _load_dataset() -> MemoryDataset:
    """Read the YAML dataset into memory.

    Inspect ships CSV and JSON loaders but not YAML, so the records are read
    here and handed over as a `MemoryDataset`. YAML earns that glue twice over:
    the documents are inline as block scalars, which keeps each record readable
    and diffable as one unit, and the rubric prose stays legible where a JSON
    string of the same length would not.
    """
    path = Path(__file__).parent / "dataset.yaml"
    records = yaml.safe_load(path.read_text())
    for record in records:
        if not record.get("expected_results") and not record.get("expects_no_results"):
            raise ValueError(
                f"dataset record {record.get('id')!r} declares no expected_results; "
                "four of the deterministic checks compare against that inventory "
                "and have nothing to check without it. A document that genuinely "
                "presents no results should say so with `expects_no_results: true`"
            )
    return MemoryDataset(
        samples=[_record_to_sample(record) for record in records],
        name="results_extraction",
        location=str(path),
    )


def _extract_result(state: TaskState) -> tuple[AgentCheckResult | None, str]:
    """Parse the workflow state into its result, or explain why it cannot be.

    Returns `(result, "")` on success and `(None, reason)` otherwise, so both
    scorers reject an unusable output the same way and for the same reasons.
    """
    try:
        output = SimpleDeepAgentOutput.model_validate_json(state.output.completion)
    except ValidationError as e:
        return None, f"Could not parse the workflow state: {e}"
    if output.result is None:
        return None, "No result in the workflow state"
    return output.result, ""


def _label_of(issue: IssueItem) -> str | None:
    """The reproducibility label in a result issue's title, lowercased."""
    match = _LABEL.search(issue.title.strip())
    if match is None:
        return None
    label = match.group(1).strip().lower()
    return label if label in REPRODUCIBILITY_LABELS else None


def _table_row_count(report: str) -> tuple[int, str]:
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


def _severity_matches_label(severity: str, label: str) -> bool:
    """The split the skill mandates, without pinning the exact level."""
    if label == NOT_REPRODUCIBLE:
        return severity in REAL_SEVERITIES
    return severity == "none"


# Reproducibility classes as the dataset spells them, mapped to the label that
# appears in an issue title.
CLASS_LABELS = {
    "fully_reproducible": "fully reproducible",
    "reproducible_with_web_search": "reproducible with web search",
    "reproducible_with_external_uploads": "reproducible with external uploads",
    "not_reproducible": "not reproducible",
}

# How much the document rests on a result, most to least. Only compared between
# non-reproducible results, and only as an ordering.
IMPORTANCE_RANK = {"central": 3, "supporting": 2, "incidental": 1}

SEVERITY_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}


def _issue_text(issue: IssueItem) -> tuple[str, str]:
    """An issue's title and its body, both lowercased, for anchor matching."""
    body = " ".join(
        part
        for part in (issue.description, issue.long_description, issue.suggested_action)
        if part
    )
    return issue.title.lower(), body.lower()


def _match_expected(
    issues: list[IssueItem], expected: list[dict[str, Any]]
) -> dict[str, int]:
    """Assign each expected result to at most one reported issue.

    An expected result matches an issue when any of its `match` substrings
    appears in the issue. Two rules decide the assignment, in order:

    1. **Title hits first.** A match in the issue's title is stronger evidence
       than one in its prose, so those pairs are settled before body-only pairs
       are considered at all.
    2. **Then maximum cardinality.** Greedy assignment used to lose valid
       pairings: when one expected result matched several issues and another
       matched only one of them, taking the first pair could strand the
       constrained result and report it missing. Augmenting paths avoid that --
       a later result can displace an earlier one onto a different issue, so the
       number of matched results is the most the anchors allow.

    One-to-one is the point: two expected results merged into a single reported
    issue leaves the second unmatched, which is what makes merging visible.
    """
    title_edges: list[set[int]] = []
    body_edges: list[set[int]] = []
    for entry in expected:
        anchors = [a.lower() for a in entry["match"]]
        titles, bodies = set(), set()
        for index, issue in enumerate(issues):
            title, body = _issue_text(issue)
            if any(a in title for a in anchors):
                titles.add(index)
            elif any(a in body for a in anchors):
                bodies.add(index)
        title_edges.append(titles)
        body_edges.append(bodies)

    # issue index -> expected index, the matching being built.
    owner: dict[int, int] = {}

    def augment(e_index: int, edges: list[set[int]], seen: set[int]) -> bool:
        """Match `e_index`, displacing already-matched results where possible."""
        for i_index in sorted(edges[e_index]):
            if i_index in seen:
                continue
            seen.add(i_index)
            if i_index not in owner or augment(owner[i_index], edges, seen):
                owner[i_index] = e_index
                return True
        return False

    # Pass 1: title hits only, so a strong pair is never displaced by a weak one.
    for e_index in range(len(expected)):
        augment(e_index, title_edges, set())

    # Pass 2: allow body hits, keeping every result matched in pass 1 matched.
    combined = [title_edges[i] | body_edges[i] for i in range(len(expected))]
    matched_now = set(owner.values())
    for e_index in range(len(expected)):
        if e_index not in matched_now:
            if augment(e_index, combined, set()):
                matched_now.add(e_index)

    return {expected[e]["id"]: i for i, e in owner.items()}


def _ground_truth_checks(
    issues: list[IssueItem],
    expected: list[dict[str, Any]],
    labels: list[str | None],
    expects_none: bool = False,
) -> dict[str, tuple[bool | float, str]]:
    """Compare the reported inventory against the dataset's expected one."""
    if expects_none:
        # The whole assertion is that nothing should be reported, so an empty
        # inventory passes all four and anything reported fails them.
        verdict = float(not issues)
        note = (
            "document presents no results and none were reported"
            if not issues
            else f"document presents no results, but {len(issues)} were reported"
        )
        return {
            key: (verdict, note)
            for key in ("completeness", "class_accuracy", "no_extras", "severity_ordering")
        }
    if not expected:
        # Every record is required to declare its inventory (`_load_dataset`
        # enforces it), so reaching here means the dataset is malformed. Failing
        # is the honest reading: scoring 1.0 would report four passes that were
        # never tested, and a sample with no ground truth cannot be checked.
        note = "no expected inventory declared -- this sample cannot be scored"
        return {
            key: (0.0, note)
            for key in ("completeness", "class_accuracy", "no_extras", "severity_ordering")
        }

    matched = _match_expected(issues, expected)
    by_id = {entry["id"]: entry for entry in expected}

    required = [e["id"] for e in expected if e.get("required", True)]
    found = [entry_id for entry_id in required if entry_id in matched]
    missing = [entry_id for entry_id in required if entry_id not in matched]
    completeness = (
        len(found) / len(required) if required else 1.0,
        (
            f"{len(found)}/{len(required)} required result(s) found"
            + (f"; missing {', '.join(missing)}" if missing else "")
        )
        if required
        else "no required results declared",
    )

    wrong_class = []
    correct = 0
    for entry_id, i_index in matched.items():
        want = CLASS_LABELS[by_id[entry_id]["class"]]
        got = labels[i_index]
        if got == want:
            correct += 1
        else:
            wrong_class.append(f"{entry_id}: {got or 'unlabelled'}, expected {want}")
    class_accuracy = (
        correct / len(matched) if matched else 0.0,
        (
            f"{correct}/{len(matched)} classified correctly"
            + (f"; {'; '.join(wrong_class)}" if wrong_class else "")
        )
        if matched
        else "no expected result was found, so nothing to classify",
    )

    # Fractional, not binary: one defensible extra reading and a run that
    # invented five results used to score the same zero, which made the metric
    # unusable for telling those apart.
    extras = [
        issues[i].title for i in range(len(issues)) if i not in set(matched.values())
    ]
    accounted = len(issues) - len(extras)
    no_extras = (
        accounted / len(issues) if issues else 0.0,
        (
            "no results reported"
            if not issues
            else (
                f"all {len(issues)} reported result(s) are in the expected inventory"
                if not extras
                else f"{len(extras)}/{len(issues)} unexpected: "
                + "; ".join(repr(e) for e in extras)
            )
        ),
    )

    # Severity ordering, over the non-reproducible results that were both found
    # and labelled as such: a result the document leans on harder must not carry
    # a lower severity than one it leans on less.
    ranked: list[tuple[int, int, str]] = []
    for entry_id, i_index in matched.items():
        entry = by_id[entry_id]
        if entry["class"] != "not_reproducible" or labels[i_index] != NOT_REPRODUCIBLE:
            continue
        ranked.append(
            (
                IMPORTANCE_RANK[entry["importance"]],
                SEVERITY_RANK.get(issues[i_index].severity, 0),
                entry_id,
            )
        )

    inversions = [
        f"{a_id} ({'>' if a_imp > b_imp else '<'} importance) is severity-ranked "
        f"{'below' if a_sev < b_sev else 'above'} {b_id}"
        for a_imp, a_sev, a_id in ranked
        for b_imp, b_sev, b_id in ranked
        if a_imp > b_imp and a_sev < b_sev
    ]
    comparable = any(
        a_imp != b_imp for a_imp, _, _ in ranked for b_imp, _, _ in ranked
    )
    severity_ordering = (
        not inversions,
        (
            "no non-reproducible results of differing importance to compare"
            if not comparable
            else (
                f"{len(ranked)} non-reproducible result(s) ordered correctly"
                if not inversions
                else "; ".join(inversions)
            )
        ),
    )

    return {
        "completeness": completeness,
        "class_accuracy": class_accuracy,
        "no_extras": no_extras,
        "severity_ordering": severity_ordering,
    }


def _inventory_checks(
    result: AgentCheckResult, meta: dict[str, Any], document_lines: int
) -> dict[str, tuple[bool | float, str]]:
    """Run every deterministic rule, each with the detail behind its verdict."""
    expected: list[dict[str, Any]] = meta.get("expected_results") or []
    expected_min = sum(1 for e in expected if e.get("required", True))
    # A document that presents no results at all inverts most of these: the
    # correct output is an empty issue list, so "no results reported" is the pass
    # rather than the vacuous case.
    expects_none: bool = bool(meta.get("expects_no_results"))
    issues = result.issues
    report = (result.report_markdown or "").strip()
    labels = [_label_of(issue) for issue in issues]
    labelled = [(issue, label) for issue, label in zip(issues, labels) if label]

    checks: dict[str, tuple[bool | float, str]] = {}

    checks["report"] = (
        len(report) >= MIN_REPORT_CHARS,
        f"{len(report)} chars (min {MIN_REPORT_CHARS})",
    )

    # The skill's report format: a table of every result. Fewer rows than
    # results means the report and the issue list disagree about the inventory.
    rows, table_kind = _table_row_count(report)
    checks["inventory_table"] = (
        (not issues) if expects_none else (bool(issues) and rows >= len(issues)),
        f"{rows} row(s) in the {table_kind} for {len(issues)} result(s)",
    )

    checks["result_count"] = (
        len(issues) >= expected_min,
        f"{len(issues)} result(s), expected at least {expected_min}",
    )

    # Every title has to carry one of the four labels, which is what makes the
    # class visible in the issue list and checkable here.
    unlabelled = [issue.title for issue, label in zip(issues, labels) if not label]
    checks["labels"] = (
        (not issues) if expects_none else (bool(issues) and not unlabelled),
        (
            "no results reported"
            if not issues
            else (
                "every title carries a label"
                if not unlabelled
                else f"{len(unlabelled)} unlabelled, e.g. {unlabelled[0]!r}"
            )
        ),
    )

    # Reproducible -> `none`, not reproducible -> a real severity. Judged over
    # the labelled results only: an unlabelled one is the `labels` check's
    # business, and failing it twice would hide how many rules actually broke.
    wrong = [
        f"{issue.title!r} is {issue.severity}"
        for issue, label in labelled
        if label and not _severity_matches_label(issue.severity, label)
    ]
    checks["severity_split"] = (
        (not issues) if expects_none else (bool(labelled) and not wrong),
        (
            "no labelled results to check"
            if not labelled
            else (
                f"{len(labelled)} result(s) split correctly"
                if not wrong
                else "; ".join(wrong)
            )
        ),
    )

    # Ordered and positive is not enough: lines 900-905 of a 100-line document
    # are as unusable as a reversed range, and the reporting tool does not check
    # the upper bound either.
    bad_ranges = [
        f"{issue.title!r} lines {issue.start_line}-{issue.end_line}"
        for issue in issues
        if issue.start_line < 1
        or issue.end_line < issue.start_line
        or issue.end_line > document_lines
    ]
    checks["line_ranges"] = (
        (not issues) if expects_none else (bool(issues) and not bad_ranges),
        (
            "no results reported"
            if not issues
            else (
                f"all line ranges land inside the document's {document_lines} lines"
                if not bad_ranges
                else f"document has {document_lines} lines; " + "; ".join(bad_ranges)
            )
        ),
    )

    # A result reported twice is one result, and duplicate titles have shown up
    # in real runs (one emitted eighteen issues with three copies of one result).
    seen: dict[str, int] = {}
    for issue in issues:
        key = issue.title.strip().lower()
        seen[key] = seen.get(key, 0) + 1
    duplicates = {title: n for title, n in seen.items() if n > 1}
    checks["no_duplicates"] = (
        not duplicates,
        "no repeated issue titles"
        if not duplicates
        else "; ".join(f"{title!r} reported {n} times" for title, n in duplicates.items()),
    )

    checks.update(_ground_truth_checks(issues, expected, labels, expects_none))
    return checks


@scorer(metrics={name: [mean(), stderr()] for name in INVENTORY_CHECKS})
def inventory_checks() -> Scorer:
    """The deterministic rules, one metric per rule.

    A single scorer returning a dict rather than six separate scorers: the
    checks share the parse of the workflow state and the label extraction, and
    Inspect reports each key as its own metric either way.
    """

    async def score(state: TaskState, target: Target) -> Score:
        result, reason = _extract_result(state)
        if result is None:
            return failed_score(INVENTORY_CHECKS, reason)
        document_lines = len(state.input_text.splitlines())
        return checks_to_score(
            _inventory_checks(result, state.metadata or {}, document_lines)
        )

    return score


def _answer_text(result: AgentCheckResult) -> str:
    """The delivery as prose for the grader: the inventory, then the report.

    The issues are rendered rather than handed over as raw state JSON, because
    what the criteria turn on -- which results were found, how each is
    classified and defended -- is what a reader of the app sees, and JSON
    punctuation would otherwise be most of the prompt.
    """
    entries = []
    for issue in result.issues:
        parts = [
            f"### {issue.title}",
            f"Severity: {issue.severity} | Lines {issue.start_line}-{issue.end_line}",
            issue.description,
        ]
        if issue.long_description:
            parts.append(issue.long_description)
        if issue.suggested_action:
            parts.append(f"Suggested action: {issue.suggested_action}")
        entries.append("\n".join(parts))

    inventory = "\n\n".join(entries) or "(no results reported)"
    return (
        f"=== RESULT INVENTORY ({len(result.issues)} reported) ===\n{inventory}\n\n"
        f"=== REPORT ===\n{result.report_markdown}\n"
    )


@scorer(metrics={name: [mean(), stderr()] for name in RUBRIC_CRITERIA})
def rubric_criteria(model: str | Model | None = None) -> Scorer:
    """Grade this suite's two criteria, each in its own grader call."""

    async def score(state: TaskState, target: Target) -> Score:
        result, reason = _extract_result(state)
        if result is None:
            return failed_score(RUBRIC_CRITERIA, reason)

        return await grade_criteria(
            grader=get_model(model) if model else get_model(GRADER_MODEL),
            keys=RUBRIC_CRITERIA,
            criteria=criteria_for(state, SHARED_CRITERIA),
            answer=_answer_text(result),
            question=state.input_text,
            # Graders disagreed with themselves across repeats of an unchanged
            # output, so each criterion is graded three times and the median
            # taken. It is the noisiest half of this suite; tokens are cheaper
            # than a metric nobody can act on.
            calls_per_criterion=3,
            # These criteria state properties the review must have, not content
            # it should contain, so they need the requirement prompt.
            template=REQUIREMENT_TEMPLATE,
        )

    return score


def _viewer_config() -> ViewerConfig:
    """Log-viewer defaults tuned to how this eval is read: which check
    regressed, and whether the workflow is stable across epochs."""
    score_columns = [
        *(
            TaskSamplesColumn.score("inventory_checks", name)
            for name in INVENTORY_CHECKS
        ),
        *(TaskSamplesColumn.score("rubric_criteria", name) for name in RUBRIC_CRITERIA),
    ]

    return ViewerConfig(
        task_samples_view=TaskSamplesView(
            name="Checks and epochs",
            columns=[
                TaskSamplesColumn(id="sampleStatus"),
                TaskSamplesColumn(id="sampleId"),
                TaskSamplesColumn(id="epoch"),
                *score_columns,
                TaskSamplesColumn(id="error"),
                TaskSamplesColumn(id="duration"),
                TaskSamplesColumn(id="input", visible=False),
                TaskSamplesColumn(id="target", visible=False),
                TaskSamplesColumn(id="answer", visible=False),
                TaskSamplesColumn(id="tokens", visible=False),
            ],
            # Group each document's epochs together: this workflow's failures
            # are run-to-run variance on one document, so repeats of the same
            # sample are the comparison worth reading side by side.
            sort=[
                TaskSamplesSort(column="sampleId", dir="asc"),
                TaskSamplesSort(column="epoch", dir="asc"),
            ],
            compact_scores=True,
            multiline=False,
            score_labels={
                "report": "Report",
                "inventory_table": "Table",
                "result_count": "Count",
                "labels": "Labels",
                "severity_split": "Split",
                "line_ranges": "Lines",
                "no_duplicates": "No dupes",
                "completeness": "Found",
                "class_accuracy": "Class",
                "no_extras": "No extras",
                "severity_ordering": "Order",
                "classification_grounded": "Grounded",
                "sample_expectations": "Sample",
            },
            # Pinned to 0..1 rather than left to the viewer's default, which
            # anchors each palette to that column's observed range: a check that
            # passes everywhere would paint nothing.
            score_color_scales={
                name: ScoreColorScale(palette="good-high", min=0.0, max=1.0)
                for name in (*INVENTORY_CHECKS, *RUBRIC_CRITERIA)
            },
            color_scales_enabled=True,
        ),
        sample_score_view=SampleScoreView(
            default="grid",
            sort=SampleScoreViewSort(column="value", dir="asc"),
        ),
    )


@task
def results_extraction_e2e():
    return Task(
        dataset=_load_dataset(),
        fail_on_error=0.2,
        solver=api_workflow_agent("results_extraction", timeout_s=600),
        scorer=[
            inventory_checks(),
            rubric_criteria(),
        ],
        viewer=_viewer_config(),
    )
