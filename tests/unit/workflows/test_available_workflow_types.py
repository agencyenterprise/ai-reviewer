"""The shared "does this persisted type still exist?" check.

Every read path that loads a stored workflow type — `workflow_runs.type`,
`issues.workflow_type` — has to answer this before handing the row to a client,
so the answer lives in one place. What the callers depend on, and what these
tests pin, is that it accepts the raw `str` those columns actually yield rather
than only the enum.
"""

from lib.workflows.models import WorkflowRunType
from lib.workflows.registry import (
    available_workflow_type_values,
    get_all_manifests,
    is_available_workflow_type,
)

# Removed in an earlier cleanup; rows carrying it are still in the database.
RETIRED_TYPE = "claim_substantiation"


def test_accepts_the_raw_strings_the_columns_yield():
    """SQLModel skips validation on table models, so `run.type` is often a str.

    A check that only worked on enum members would silently pass every row read
    back from the database.
    """
    live = WorkflowRunType.RECOMMENDATION_CHECK

    assert is_available_workflow_type(live)
    assert is_available_workflow_type(live.value)
    assert is_available_workflow_type("recommendation_check")


def test_retired_types_are_unavailable_in_both_forms():
    assert not is_available_workflow_type(RETIRED_TYPE)
    # A slug that never existed behaves the same as one that was retired.
    assert not is_available_workflow_type("never_a_workflow")


def test_values_list_matches_the_predicate():
    """The SQL-filter form and the per-item form must not drift apart."""
    values = available_workflow_type_values()

    assert values, "expected at least one registered workflow"
    assert all(is_available_workflow_type(v) for v in values)
    assert set(values) == {t.value for t in get_all_manifests()}
    assert RETIRED_TYPE not in values
