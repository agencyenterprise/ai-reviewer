"""Admin usage dashboard endpoint."""

import aiotools
from fastapi import APIRouter, Depends, Query

from lib.api.auth import require_admin
from lib.models.user import User
from lib.services.admin_dashboard.models import AdminDashboardResponse
from lib.services.admin_dashboard.service import get_admin_dashboard

router = APIRouter(prefix="/api/admin", tags=["admin-dashboard"])

# Cache the aggregate (a set of sequential scans over workflow_runs) at the
# endpoint layer, the same way the duration estimates endpoint does. Five
# minutes on a figure that counts whole days is invisible to the reader, and the
# response carries the `period_end` it was computed for, so the page's "as of"
# line stays honest about what it is showing.
#
# aiotools.lru_cache wraps async-lru, which caches the in-flight task: callers
# arriving during a miss await the same computation rather than starting their
# own. That is what keeps a refresh-happy admin — or several — down to one set
# of scans per window per interval.
_CACHE_TTL_SECONDS = 300

# The UI offers four windows; the cap keeps a caller who churns `days` values
# from growing the cache without bound.
_CACHE_MAXSIZE = 16


@aiotools.lru_cache(maxsize=_CACHE_MAXSIZE, expire_after=_CACHE_TTL_SECONDS)
async def _cached_dashboard(days: int) -> AdminDashboardResponse:
    return await get_admin_dashboard(days)


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

    Served from a five-minute cache (see `_cached_dashboard`); `period_end` in
    the response is the moment the figures were computed.
    """
    return await _cached_dashboard(days)
