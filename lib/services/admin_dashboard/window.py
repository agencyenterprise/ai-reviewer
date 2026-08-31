"""The time window every dashboard aggregate is computed over."""

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel

from lib.services.admin_dashboard.models import ActivityGranularity

# Past three months a per-day bar chart stops being readable (and the series
# stops fitting the card), so longer windows are bucketed by week.
_WEEKLY_BUCKET_THRESHOLD_DAYS = 92


class DashboardWindow(BaseModel):
    """The selected window plus the equal-length one preceding it.

    `previous_start` exists so a single query can count both windows with
    conditional aggregation instead of running twice.
    """

    days: int
    start: datetime
    end: datetime
    previous_start: datetime
    granularity: ActivityGranularity

    @classmethod
    def for_days(cls, days: int) -> "DashboardWindow":
        end = datetime.now(timezone.utc)
        span = timedelta(days=days)
        return cls(
            days=days,
            start=end - span,
            end=end,
            previous_start=end - 2 * span,
            granularity=(
                ActivityGranularity.WEEK
                if days > _WEEKLY_BUCKET_THRESHOLD_DAYS
                else ActivityGranularity.DAY
            ),
        )
