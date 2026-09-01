"""Pairing the results the workflow reported with the ones the dataset expects.

One-to-one, by the `match` anchors each expected result carries. This is the part
of the scorer that has misjudged correct output most often, so the rules it
follows are spelled out in `match_expected`.
"""

from typing import Any

from evals_inspectai.common.simple_deep_agent_types import IssueItem

def _issue_text(issue: IssueItem) -> tuple[str, str]:
    """An issue's title and its body, both lowercased, for anchor matching."""
    body = " ".join(
        part
        for part in (issue.description, issue.long_description, issue.suggested_action)
        if part
    )
    return issue.title.lower(), body.lower()


def match_expected(
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

    combined = [title_edges[i] | body_edges[i] for i in range(len(expected))]

    # issue index -> expected index, the matching being built.
    owner: dict[int, int] = {}

    def augment(e_index: int, seen: set[int], allow_body: bool) -> bool:
        """Match `e_index`, displacing already-matched results where possible.

        `allow_body` is False for a result that currently holds a title hit: it
        may be re-homed onto another title hit, but never demoted onto a body
        hit. Without that restriction an unmatched result could push a
        title-matched one onto a body-only issue, which raises the match count
        while attributing both classifications to the wrong ground-truth
        results -- a worse outcome than leaving the second result unmatched.
        """
        edges = combined[e_index] if allow_body else title_edges[e_index]
        for i_index in sorted(edges):
            if i_index in seen:
                continue
            seen.add(i_index)
            holder = owner.get(i_index)
            if holder is None:
                owner[i_index] = e_index
                return True
            holder_on_title = i_index in title_edges[holder]
            if augment(holder, seen, allow_body=not holder_on_title):
                owner[i_index] = e_index
                return True
        return False

    # Pass 1: title hits only, so every title pairing that can be made, is.
    for e_index in range(len(expected)):
        augment(e_index, set(), allow_body=False)

    # Pass 2: the rest, by body hit, without disturbing any title pairing.
    matched_now = set(owner.values())
    for e_index in range(len(expected)):
        if e_index not in matched_now and augment(e_index, set(), allow_body=True):
            matched_now.add(e_index)

    return {expected[e]["id"]: i for i, e in owner.items()}

