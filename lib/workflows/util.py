from collections.abc import Iterable
from typing import TYPE_CHECKING

from lib.workflows.models import BaseWorkflowState, WorkflowRunType

if TYPE_CHECKING:
    from lib.workflows.workflow_types import WorkflowState


def get_state_by_type[StateType: BaseWorkflowState](
    run_type: WorkflowRunType,
    state_type: type[StateType],
    states: Iterable["WorkflowState"],
) -> StateType | None:
    """
    Get the state of a workflow run type from a list of states, as its state class.
    """

    for state in states:
        if state.type == run_type:
            return as_state_type(state, state_type)
    return None


def as_state_type[StateType: BaseWorkflowState](
    state: BaseWorkflowState, state_type: type[StateType]
) -> StateType:
    """
    Narrow a hydrated workflow state to the class its run type is stored as.

    A run's state is always hydrated with its manifest's state class, so a
    mismatch means the caller named the wrong class for the run type.
    """

    if not isinstance(state, state_type):
        raise TypeError(
            f"Expected a {state_type.__name__}, got a {type(state).__name__}"
        )
    return state
