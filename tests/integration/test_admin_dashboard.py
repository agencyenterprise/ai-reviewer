"""Integration tests for the admin usage dashboard aggregates.

Runs against the real database. Isolation comes from the fixture's own user and
from a workflow type slug that exists nowhere else, so the per-workflow and
per-user assertions are exact even though the aggregates are global. The
window-wide totals are asserted as lower bounds around the fixture's rows.

The fixture deliberately inserts both a retired slug (no manifest) and a live
assessment slug: the two are counted differently, and that difference is the
thing most likely to break.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlmodel import col

from lib.config.database import get_async_db_session
from lib.models.feedback import Feedback, FeedbackType
from lib.models.project import FeedbackVisibility, Project
from lib.models.user import User, UserRole
from lib.models.workflow_run import WorkflowRun, WorkflowRunStatus
from lib.services.admin_dashboard import queries
from lib.services.admin_dashboard.service import (
    CACHE_TTL_SECONDS,
    get_admin_dashboard,
)
from lib.services.admin_dashboard.window import DashboardWindow
from lib.workflows.models import WorkflowRunType

NOW = datetime.now(timezone.utc)

# A live, user-selectable workflow: these are what the assessment metrics count.
ASSESSMENT_SLUG = WorkflowRunType.FIGURES_TABLES_CHECK.value


class _Fixture:
    """Everything the fixture inserted, plus the slug that isolates it."""

    def __init__(self, user: User, project: Project, slug: str):
        self.user = user
        self.project = project
        self.slug = slug


def _run(
    project_id: uuid.UUID,
    slug: str,
    status: WorkflowRunStatus,
    created_at: datetime,
    duration_seconds: float | None = None,
) -> WorkflowRun:
    started_at = created_at if duration_seconds is not None else None
    completed_at = (
        created_at + timedelta(seconds=duration_seconds)
        if duration_seconds is not None
        else None
    )
    return WorkflowRun(
        id=uuid.uuid4(),
        project_id=project_id,
        type=slug,  # type: ignore[arg-type]  # a retired slug: the column is a plain string
        langgraph_thread_id=str(uuid.uuid4()),
        status=status,
        created_at=created_at,
        last_updated_at=created_at,
        started_at=started_at,
        completed_at=completed_at,
    )


@pytest_asyncio.fixture
async def dashboard_data():
    """A user with runs of both a retired and a live workflow type, and feedback.

    Four retired-slug runs sit inside a one-day window plus one ten days back,
    and three live-assessment runs sit inside it.
    """
    tag = str(uuid.uuid4()).replace("-", "")[:12]
    slug = f"dashboard_test_{tag}"

    user = User(
        id=uuid.uuid4(),
        email=f"dash-{tag}@example.com",
        name=f"Dash {tag}",
        role=UserRole.USER,
        show_experimental_features=False,
        created_at=NOW - timedelta(hours=1),
        last_updated_at=NOW - timedelta(hours=1),
    )
    project = Project(
        id=uuid.uuid4(),
        title=f"Dashboard project {tag}",
        user_id=user.id,
        created_at=NOW - timedelta(hours=1),
        last_updated_at=NOW - timedelta(hours=1),
        feedback_visibility=FeedbackVisibility.FULL_PROJECT,
    )
    runs = [
        _run(project.id, slug, WorkflowRunStatus.COMPLETED, NOW - timedelta(hours=3), 10),
        _run(project.id, slug, WorkflowRunStatus.COMPLETED, NOW - timedelta(hours=2), 30),
        _run(project.id, slug, WorkflowRunStatus.FAILED, NOW - timedelta(hours=1)),
        _run(project.id, slug, WorkflowRunStatus.RUNNING, NOW - timedelta(minutes=30)),
        # Outside a one-day window: must not be counted.
        _run(project.id, slug, WorkflowRunStatus.COMPLETED, NOW - timedelta(days=10), 99),
        # A live assessment type — the only runs here the assessment metrics count.
        _run(project.id, ASSESSMENT_SLUG, WorkflowRunStatus.COMPLETED, NOW - timedelta(hours=2), 5),
        _run(project.id, ASSESSMENT_SLUG, WorkflowRunStatus.COMPLETED, NOW - timedelta(hours=1), 7),
        _run(project.id, ASSESSMENT_SLUG, WorkflowRunStatus.FAILED, NOW - timedelta(minutes=45)),
    ]
    feedbacks = [
        Feedback(
            id=uuid.uuid4(),
            workflow_run_id=runs[0].id,
            user_id=user.id,
            entity_path={},
            feedback_type=FeedbackType.THUMBS_UP,
            created_at=NOW - timedelta(minutes=20),
            updated_at=NOW - timedelta(minutes=20),
        ),
        Feedback(
            id=uuid.uuid4(),
            workflow_run_id=runs[1].id,
            user_id=user.id,
            entity_path={},
            feedback_type=FeedbackType.THUMBS_DOWN,
            feedback_text="Missed a citation",
            created_at=NOW - timedelta(minutes=10),
            updated_at=NOW - timedelta(minutes=10),
        ),
    ]

    # Committed in FK order: nothing declares a relationship() between these
    # models, so the unit of work has no dependency graph to sort inserts by.
    async with get_async_db_session() as session:
        session.add(user)
        await session.commit()
        session.add(project)
        await session.commit()
        for run in runs:
            session.add(run)
        await session.commit()
        for feedback in feedbacks:
            session.add(feedback)
        await session.commit()

    yield _Fixture(user, project, slug)

    async with get_async_db_session() as session:
        for model, ids in (
            (Feedback, [f.id for f in feedbacks]),
            (WorkflowRun, [r.id for r in runs]),
            (Project, [project.id]),
            (User, [user.id]),
        ):
            for row_id in ids:
                found = (
                    await session.execute(select(model).where(col(model.id) == row_id))
                ).scalar_one_or_none()
                if found is not None:
                    await session.delete(found)
        await session.commit()


@pytest.mark.asyncio
async def test_workflow_usage_reports_outcomes_and_median_duration(dashboard_data):
    response = await get_admin_dashboard(days=1)

    item = next(w for w in response.workflows if w.type == dashboard_data.slug)

    assert item.runs == 4  # the ten-day-old run is outside the window
    assert item.statuses.completed == 2
    assert item.statuses.failed == 1
    assert item.statuses.running == 1
    assert item.median_duration_seconds == pytest.approx(20.0)
    assert item.is_retired is True
    assert item.is_internal is False
    assert item.name == dashboard_data.slug.replace("_", " ").title()


@pytest.mark.asyncio
async def test_workflow_usage_attributes_feedback_to_the_run_type(dashboard_data):
    response = await get_admin_dashboard(days=1)

    item = next(w for w in response.workflows if w.type == dashboard_data.slug)

    assert item.thumbs_up == 1
    assert item.thumbs_down == 1


@pytest.mark.asyncio
async def test_top_users_counts_only_live_assessment_runs(dashboard_data):
    """The four retired-slug runs must not be attributed to the user."""
    window = DashboardWindow.for_days(1)

    async with get_async_db_session() as session:
        rows = await queries.get_top_users(session, window, limit=1000)

    row = next(r for r in rows if r.user_id == dashboard_data.user.id)

    assert row.workflow_runs == 3
    assert row.projects == 1
    assert row.email == dashboard_data.user.email
    assert row.last_active_at is not None


@pytest.mark.asyncio
async def test_activity_series_is_dense_and_covers_the_window(dashboard_data):
    response = await get_admin_dashboard(days=7)

    buckets = [point.bucket for point in response.activity]

    assert len(buckets) == len(set(buckets))
    assert buckets == sorted(buckets)
    assert buckets[-1] == response.period_end.date()
    assert sum(point.workflow_runs for point in response.activity) >= 3


@pytest.mark.asyncio
async def test_fixture_rows_move_the_totals(dashboard_data):
    response = await get_admin_dashboard(days=1)

    assert response.active_users.current >= 1
    assert response.new_users.current >= 1
    assert response.projects_created.current >= 1
    assert response.assessments_run.current >= 3
    assert response.feedback_received.current >= 2
    assert response.feedback.thumbs_up >= 1
    assert response.feedback.thumbs_down >= 1
    assert response.feedback.with_comment >= 1
    assert response.total_users >= 1
    assert response.period_days == 1


@pytest.mark.asyncio
async def test_response_advertises_the_real_cache_window(dashboard_data):
    """The page prints this number to the reader, so it cannot be a guess."""
    response = await get_admin_dashboard(days=1)

    assert response.cache_ttl_seconds == CACHE_TTL_SECONDS


@pytest.mark.asyncio
async def test_only_one_computation_runs_at_a_time(dashboard_data, monkeypatch):
    """The guard that keeps this page from slowing the rest of the app down.

    Each computation holds one connection from a pool of 8 (+3 overflow) that
    every other request shares, so concurrent callers have to queue rather than
    compete. Without the semaphore in the service, 25 concurrent requests took
    an ordinary /api/projects call from 24 ms to 780 ms.
    """
    in_flight = 0
    peak = 0
    real_get_user_metrics = queries.get_user_metrics

    async def counting_get_user_metrics(session, window):
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        try:
            # An await point inside the guarded section: if two computations
            # could overlap, this is where they would.
            await asyncio.sleep(0.02)
            return await real_get_user_metrics(session, window)
        finally:
            in_flight -= 1

    monkeypatch.setattr(queries, "get_user_metrics", counting_get_user_metrics)

    responses = await asyncio.gather(
        *[get_admin_dashboard(days=1) for _ in range(6)]
    )

    assert peak == 1
    assert len(responses) == 6
    assert all(response.period_days == 1 for response in responses)
