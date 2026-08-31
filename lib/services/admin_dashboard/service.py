"""Assembles the admin usage dashboard payload."""

import asyncio
import logging

from lib.config.database import get_async_db_session
from lib.services.admin_dashboard import queries
from lib.services.admin_dashboard.models import AdminDashboardResponse
from lib.services.admin_dashboard.window import DashboardWindow

logger = logging.getLogger(__name__)

# Enough rows to see who is driving usage without turning the card into the
# user-management table, which already exists at /users.
_TOP_USERS_LIMIT = 10


async def get_admin_dashboard(days: int) -> AdminDashboardResponse:
    """Every dashboard aggregate for a rolling window of `days`.

    The aggregates are independent, but they share one session and run
    sequentially: they are all scans of the same few tables, and the async
    engine's pool is small enough that fanning one request across several
    connections is the wrong trade.
    """
    window = DashboardWindow.for_days(days)

    async with get_async_db_session() as session:
        total_users, new_users = await queries.get_user_metrics(session, window)
        projects_created = await queries.get_project_metrics(session, window)
        assessments_run = await queries.get_assessment_metrics(session, window)
        active_users = await queries.get_active_user_metrics(session, window)
        feedback_received, feedback = await queries.get_feedback_metrics(
            session, window
        )
        activity = await queries.get_activity(session, window)
        workflows = await queries.get_workflow_usage(session, window)
        top_users = await queries.get_top_users(session, window, _TOP_USERS_LIMIT)

    return AdminDashboardResponse(
        period_days=window.days,
        period_start=window.start,
        period_end=window.end,
        granularity=window.granularity,
        total_users=total_users,
        active_users=active_users,
        new_users=new_users,
        projects_created=projects_created,
        assessments_run=assessments_run,
        feedback_received=feedback_received,
        activity=activity,
        workflows=workflows,
        top_users=top_users,
        feedback=feedback,
    )
