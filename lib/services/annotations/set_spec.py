"""What an annotation set is, and the question every set asks.

A set is defined in code (one module per eval under ``sets/``) and written to
the database by the sync. Each is built from an issue-inventory eval dataset:
every expected issue and every decoy with an anchor becomes one item, which by
default asks "should this passage be flagged?". A set that asks something else
overrides ``issue_reference`` and ``decoy_reference``.
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from evals_inspectai.common.issue_inventory import Decoy, ResolvedIssue
from lib.services.annotations.models import AnnotationOption, AnnotationQuestion

EVALS_ROOT = Path(__file__).resolve().parents[3] / "evals_inspectai" / "e2e"

SHOULD_FLAG = "should_flag"


class ItemReference(BaseModel):
    """How the dataset answers an item, and why, for the admin results view."""

    answers: dict[str, str]
    explanation: str


def with_rationale(explanation: str, rationale: Optional[str]) -> str:
    """The explanation followed by the labeller's own account, when the dataset has one."""
    return f"{explanation} {rationale.strip()}" if rationale else explanation


class AnnotationSetSpec(BaseModel):
    """A set's definition in code; the sync writes it to the database."""

    slug: str
    title: str
    workflow_type: str
    summary: str
    guidance: str
    questions: list[AnnotationQuestion]
    decoy_reasons: dict[str, str] = Field(
        default_factory=dict,
        description="Plain-language reading of each decoy reason, for the admin results view",
    )
    single_issue_kind: bool = Field(
        default=False,
        description=(
            "The check reports one kind of issue, so a decoy titled with it must not be "
            "flagged at all, and still has a single answer"
        ),
    )

    def issue_reference(self, issue: ResolvedIssue) -> Optional[ItemReference]:
        """The dataset's answer for an anchored expected issue, or None when it has no single one."""
        # An optional issue is borderline by design, so neither answer is the dataset's.
        if not issue.required:
            return None
        flagged_as = f" as “{issue.title}”" if issue.title else ""
        return ItemReference(
            answers={SHOULD_FLAG: "yes"},
            explanation=with_rationale(
                f"Our test case expects Draft Detective to flag this{flagged_as}.",
                issue.rationale,
            ),
        )

    def decoy_reference(self, decoy: Decoy) -> Optional[ItemReference]:
        """The dataset's answer for a decoy, or None when it has no single one."""
        # A titled decoy may rightly be reported under another kind, so "should it
        # be flagged at all?" has no single answer, unless that is the only kind.
        if decoy.title is not None and not self.single_issue_kind:
            return None
        return ItemReference(
            answers={SHOULD_FLAG: "no"},
            explanation=with_rationale(
                f"Our test case expects Draft Detective to leave this alone: {self.decoy_reading(decoy)}.",
                decoy.rationale,
            ),
        )

    def decoy_reading(self, decoy: Decoy) -> str:
        return self.decoy_reasons.get(decoy.reason, decoy.reason.replace("_", " "))

    @property
    def dataset_path(self) -> Path:
        return EVALS_ROOT / self.slug / "dataset.yaml"


# One wording for every set: the rules that make it specific sit right below it.
SHOULD_FLAG_PROMPT = (
    "Should Draft Detective flag the highlighted passage according to the rules below?"
)


def should_flag_question() -> AnnotationQuestion:
    return AnnotationQuestion(
        key=SHOULD_FLAG,
        prompt=SHOULD_FLAG_PROMPT,
        options=[
            AnnotationOption(value="yes", label="Yes, flag it", shortcut="1"),
            AnnotationOption(value="no", label="No, leave it", shortcut="2"),
            AnnotationOption(value="unsure", label="Not sure", shortcut="3"),
        ],
        abstain_value="unsure",
    )
