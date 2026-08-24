"""
Document analysis endpoints
"""

from fastapi import APIRouter, Depends

from lib.api.auth import get_current_user
from lib.models.user import User
from lib.services.preflight.models import PreflightRequest, PreflightResult
from lib.services.preflight.service import preflight_service

router = APIRouter(tags=["analysis"])


@router.post("/api/preflight", response_model=PreflightResult)
async def check_preflight(
    request: PreflightRequest,
    user: User = Depends(get_current_user),
):
    """Run preflight validation before starting analysis."""
    return await preflight_service.validate(request)
