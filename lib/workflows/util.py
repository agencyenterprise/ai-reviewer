from typing import TYPE_CHECKING

from lib.workflows.models import WorkflowRunType

if TYPE_CHECKING:
    from lib.workflows.workflow_types import WorkflowState


def get_state_by_type(
    type: WorkflowRunType, states: list["WorkflowState"]
) -> "WorkflowState | None":
    """
    Get a state by type from a list of states.
    """

    for state in states:
        if state.type == type:
            return state
    return None
