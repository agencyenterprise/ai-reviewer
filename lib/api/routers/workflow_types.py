from typing import Optional

import aiotools
from fastapi import APIRouter, Depends

from lib.api.auth import get_current_user_optional
from lib.models.user import User
from lib.services.workflow_duration_estimates import (
    WorkflowDurationEstimatesResponse,
    get_workflow_duration_estimates,
)
from lib.services.workflow_types import (
    WorkflowTypesResponse,
    get_workflow_types_for_user,
)

router = APIRouter(tags=["workflow-types"])

# Cache the duration-estimates aggregate (a full workflow_runs scan) at the
# endpoint layer. aiotools.lru_cache is functools.lru_cache for coroutines and
# adds a TTL, so the heavy query runs at most once per hour. Keyed by project_id
# so it stays correct once estimates become project-specific.
_ESTIMATES_CACHE_TTL_SECONDS = 3600


@aiotools.lru_cache(maxsize=128, expire_after=_ESTIMATES_CACHE_TTL_SECONDS)
async def _cached_duration_estimates(
    project_id: str,
) -> WorkflowDurationEstimatesResponse:
    return await get_workflow_duration_estimates(project_id)


@router.get("/api/workflow-types", response_model=WorkflowTypesResponse)
async def get_workflow_types(user: Optional[User] = Depends(get_current_user_optional)):
    """
    List available workflow types and ordered category display config based on user permissions.

    QA Screener workflows are only visible to RAND and ADMIN roles.
    """
    return get_workflow_types_for_user(user)


@router.get(
    "/api/workflow-types/duration-estimates",
    response_model=WorkflowDurationEstimatesResponse,
)
async def get_duration_estimates(
    project_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Estimated run duration for every workflow type, derived from past runs.

    Lets the UI show a ballpark "how long will this take" before a workflow is
    started. `project_id` is accepted for future project-specific refinement but
    is not yet factored into the estimate. The response is cached for an hour at
    the endpoint layer (see `_cached_duration_estimates`).
    """
    return await _cached_duration_estimates(project_id)
