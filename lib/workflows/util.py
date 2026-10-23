from collections.abc import Iterable
from typing import TYPE_CHECKING, Literal, get_args, get_origin

from lib.workflows.models import BaseWorkflowState, WorkflowRunType

if TYPE_CHECKING:
    from lib.workflows.workflow_types import WorkflowState


def pinned_run_type(state_type: type[BaseWorkflowState]) -> WorkflowRunType | None:
    """
    The run type a state class pins with ``type: Literal[WorkflowRunType.X]``.

    None for a state shared across run types, like the simple deep agents'.
    """

    field = state_type.model_fields.get("type")
    annotation = field.annotation if field is not None else None
    if get_origin(annotation) is not Literal:
        return None
    (run_type,) = get_args(annotation)
    return run_type


def run_type_of(state_type: type[BaseWorkflowState]) -> WorkflowRunType:
    """The run type a state class pins, for lookups that find a run by its state."""

    run_type = pinned_run_type(state_type)
    if run_type is None:
        raise TypeError(
            f"{state_type.__name__} does not pin its run type with a Literal, "
            "so it cannot name the run to look up"
        )
    return run_type


def get_state_by_type[StateType: BaseWorkflowState](
    state_type: type[StateType],
    states: Iterable["WorkflowState"],
) -> StateType | None:
    """
    Get the state of the run type a state class pins from a list of states.
    """

    run_type = run_type_of(state_type)
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
