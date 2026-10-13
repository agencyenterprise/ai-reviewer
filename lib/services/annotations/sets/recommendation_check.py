"""The Recommendation Check annotation set; guidance paraphrases its skill for a person.

The check reports every recommendation, classified by how well the document's
own findings support it. The set asks whether a recommendation should be raised
as a problem: partially supported and unsupported ones should, supported ones
should not. Its actionability, audience and length issues ask different
questions and are left out.
"""

from typing import Optional

from evals_inspectai.common.issue_inventory import ResolvedIssue
from lib.services.annotations.set_spec import (
    SHOULD_FLAG,
    AnnotationSetSpec,
    ItemReference,
    should_flag_question,
)

# The severity the skill reports each classification with, as the dataset labels it.
SUPPORT_BY_SEVERITY = {
    "none": "supported",
    "medium": "partially supported",
    "high": "unsupported",
}


class RecommendationSupportSpec(AnnotationSetSpec):
    """Flags a recommendation its findings do not fully support."""

    def issue_reference(self, issue: ResolvedIssue) -> Optional[ItemReference]:
        # Titled issues are the actionability, audience and length ones; an
        # unlabelled severity leaves the classification open.
        support = SUPPORT_BY_SEVERITY.get(issue.severity or "")
        if issue.title is not None or not issue.required or support is None:
            return None
        flag = issue.severity != "none"
        outcome = "flag it" if flag else "leave it alone"
        return ItemReference(
            answers={SHOULD_FLAG: "yes" if flag else "no"},
            explanation=(
                f"Our test case classifies this recommendation as {support} by the "
                f"document's findings, so it expects Draft Detective to {outcome}."
            ),
        )


RECOMMENDATION_CHECK = RecommendationSupportSpec(
    slug="recommendation_check",
    title="Recommendation Check",
    workflow_type="recommendation_check",
    summary="Do the document's own findings back the highlighted recommendation as it is worded?",
    guidance="""\
Read the whole document, then find the findings the highlighted recommendation rests on. A finding is evidence, analysis or data presented in the document itself; a citation to other work alone does not count. Check figures too: a finding may live in a chart rather than in the text. Judge each statement of a recommendation on its own wording, even when the document restates it elsewhere.

The check flags a recommendation the findings do not fully back:

- **Partially supported:** a finding backs the direction, but the recommendation adds a number or deadline no finding establishes, covers more or less than the findings do, or extends from a studied site or group to a closely related one that was not measured.
- **Unsupported:** the recommendation applies to a population, place or domain the findings never covered, no finding addresses its subject at all, or the findings contradict it.

It leaves these alone:

- A recommendation a finding backs as worded, including any number, threshold, time frame or scope it states.
- A passage that is not a recommendation: one that restates a finding, describes the study or states its limits without calling on anyone to act, even inside a Conclusions section.

Whether a recommendation is actionable, names who should act, or belongs to too long a list is a separate question and not asked here.
""",
    questions=[should_flag_question()],
    decoy_reasons={
        "conclusion": "it is a conclusion restating findings, not a recommendation",
        "concrete_action": "it names a concrete action",
        "hedged_concrete": "it is hedged but names a concrete action",
        "unquantified_action": "it names a concrete action without a number, which is fine",
        "heading_audience": "its heading names who should act",
        "lead_in_audience": "its lead-in names who should act",
        "single_actor": "the document is about one organization, which is evidently who acts",
        "restatements_counted_once": "restatements count as one recommendation",
        "sub_items": "sub-items count as part of the recommendation they elaborate",
        "three_or_fewer": "the document makes three or fewer recommendations",
    },
)
