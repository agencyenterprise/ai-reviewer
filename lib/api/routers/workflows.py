from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from lib.api.auth import get_current_user
from lib.api.models import (
    ApproveWorkflowResponse,
    CancelWorkflowResponse,
    StartMultipleWorkflowsRequest,
    StartMultipleWorkflowsResponse,
    StartWorkflowResponse,
)
from lib.api.services.workflow_runner import (
    resume_workflow_run,
    start_multiple_workflow_runs,
    start_workflow_run,
)
from lib.models.user import User
from lib.models.workflow_run import WorkflowRun, WorkflowRunStatus
from lib.services.workflow_runs import (
    hydrate_workflow_run_state_with_status,
    WorkflowRunDetail,
    cancel_workflow_run,
    get_workflow_run,
)
from lib.workflows.human_approval.state import HumanApprovalConfig
from lib.workflows.registry import get_workflow_manifest
from lib.workflows.workflow_types import WorkflowConfig

router = APIRouter(tags=["workflows"])


class RawWorkflowStateResponse(BaseModel):
    """A run's persisted state exactly as stored."""

    workflow_run_id: str
    type: str
    state_json: dict[str, Any] | None


def _assert_workflow_type_still_exists(run: WorkflowRun) -> None:
    """404 for a run whose workflow no longer exists.

    Retired types are filtered out of the project listings, so serving them here
    would be the one way to reach a run the rest of the API pretends is gone —
    and `WorkflowRunDetail.run.type` cannot even serialize once the enum member
    is dropped.
    """
    if get_workflow_manifest(run.type, raise_exception=False) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow type '{run.type}' is no longer available",
        )


@router.post("/api/workflows/start", response_model=StartWorkflowResponse)
async def start_workflow(
    request: WorkflowConfig,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Start a workflow"""

    workflow_run_id = await start_workflow_run(
        config=request, user=user, background_tasks=background_tasks
    )

    return StartWorkflowResponse(
        project_id=request.project_id,
        workflow_run_id=workflow_run_id,
        type=request.type,
        message=f"Workflow started. Track progress by polling the workflow result endpoint `/api/workflows/{workflow_run_id}`.",
    )


@router.post(
    "/api/workflows/start-multiple", response_model=StartMultipleWorkflowsResponse
)
async def start_multiple_workflows(
    request: StartMultipleWorkflowsRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Start multiple workflow analyses for a project."""

    workflow_run_ids = await start_multiple_workflow_runs(
        workflow_types=request.workflow_types,
        request=request,
        user=user,
        background_tasks=background_tasks,
    )

    return StartMultipleWorkflowsResponse(
        project_id=request.project_id,
        types=request.workflow_types,
        workflow_run_ids=workflow_run_ids,
        message="Workflows started. Track progress by polling the project endpoint `/api/project/{project_id}`.",
    )


@router.get("/api/workflows/{workflow_run_id}", response_model=WorkflowRunDetail)
async def get_workflow_state(
    workflow_run_id: str, user: User = Depends(get_current_user)
):
    """Get the state of a workflow"""

    run = await get_workflow_run(workflow_run_id, user=user, include_state=True)
    _assert_workflow_type_still_exists(run)
    state, status = hydrate_workflow_run_state_with_status(run)
    return WorkflowRunDetail(run=run, state=state, state_status=status)


@router.get(
    "/api/workflows/{workflow_run_id}/raw-state",
    response_model=RawWorkflowStateResponse,
)
async def get_workflow_raw_state(
    workflow_run_id: str, user: User = Depends(get_current_user)
):
    """The run's persisted state exactly as stored, bypassing the state model.

    Served on its own route rather than inlined into the run listings: payloads
    reach several MB, and this is only ever needed for the one run a user is
    looking at. The UI offers it when a run's state no longer validates against
    the current model, so the data is still recoverable after an assessment
    changes shape.
    """
    run = await get_workflow_run(workflow_run_id, user=user, include_state=True)
    _assert_workflow_type_still_exists(run)
    # `run.type` is a raw str when loaded from the DB (SQLModel skips validation
    # on table models) but a WorkflowRunType when built in Python, and
    # `str(WorkflowRunType.X)` is "WorkflowRunType.X", not the slug. Take .value
    # when it is there so the response always carries the persisted slug.
    return RawWorkflowStateResponse(
        workflow_run_id=str(run.id),
        type=getattr(run.type, "value", run.type),
        state_json=run.state_json,
    )


@router.post(
    "/api/workflow-runs/{workflow_run_id}/approve",
    response_model=ApproveWorkflowResponse,
)
async def approve_workflow_run(
    workflow_run_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Approve a workflow run that requires human approval.

    The workflow must:
    1. Exist and belong to a project owned by the current user
    2. Be a workflow type that supports human approval (requires_human_trigger=True)

    This unblocks any dependent workflows (e.g., CLAIM_REFERENCE_VALIDATION_V2).
    """
    workflow_run = await get_workflow_run(workflow_run_id, user=current_user)

    # Validate this workflow type supports human approval
    manifest = get_workflow_manifest(workflow_run.type)
    if not manifest.requires_human_trigger:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow type '{workflow_run.type.value}' does not require human approval",
        )

    if workflow_run.status == WorkflowRunStatus.COMPLETED:
        return ApproveWorkflowResponse(
            message="Already approved",
            workflow_run_id=workflow_run_id,
        )

    approval_config = HumanApprovalConfig(
        project_id=str(workflow_run.project_id),
    )

    await resume_workflow_run(
        workflow_run, approval_config, current_user, background_tasks
    )

    return ApproveWorkflowResponse(
        message="Workflow approved",
        workflow_run_id=workflow_run_id,
    )


@router.post(
    "/api/workflow-runs/{workflow_run_id}/cancel",
    response_model=CancelWorkflowResponse,
)
async def cancel_workflow_run_endpoint(
    workflow_run_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Cancel a workflow run that is pending or running.

    Cascades cancellation to any active workflow runs that have the cancelled
    workflow as a required dependency.
    """
    workflow_run = await get_workflow_run(workflow_run_id, user=current_user)

    if workflow_run.status == WorkflowRunStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a workflow that has already completed",
        )

    if workflow_run.status == WorkflowRunStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a workflow that has already failed",
        )

    if workflow_run.status == WorkflowRunStatus.CANCELLED:
        return CancelWorkflowResponse(
            message="Already cancelled",
            workflow_run_id=workflow_run_id,
        )

    await cancel_workflow_run(workflow_run_id, str(workflow_run.project_id))

    return CancelWorkflowResponse(
        message="Workflow cancellation requested",
        workflow_run_id=workflow_run_id,
    )
