"""Admin usage dashboard endpoint."""

from fastapi import APIRouter, Depends, Query

from lib.api.auth import require_admin
from lib.models.user import User
from lib.services.admin_dashboard.models import AdminDashboardResponse
from lib.services.admin_dashboard.service import get_admin_dashboard

router = APIRouter(prefix="/api/admin", tags=["admin-dashboard"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_dashboard(
    days: int = Query(
        default=30,
        ge=1,
        le=730,
        description="Length of the rolling window, in days.",
    ),
    _admin: User = Depends(require_admin),
) -> AdminDashboardResponse:
    """Usage aggregates for the admin dashboard over a rolling window.

    Counts are paired with the equal-length window that preceded them so the UI
    can show a trend. Feedback is reported as counts only; text and authorship
    remain behind the per-project visibility rules of `/api/admin/feedbacks`.
    """
    return await get_admin_dashboard(days)
