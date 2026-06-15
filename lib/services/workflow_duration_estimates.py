"""Pre-run duration estimates for workflow types.

Estimates are derived empirically from the wall-clock duration of past
COMPLETED runs (`completed_at - started_at`), aggregated per workflow type.

The aggregate scans the whole `workflow_runs` history. Callers that serve this
on a hot path (e.g. the API endpoint) are expected to cache the result; this
module always recomputes.
"""

import logging

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlmodel import and_, col

from lib.config.database import get_async_db_session
from lib.models.workflow_run import WorkflowRun, WorkflowRunStatus
from lib.workflows.models import WorkflowRunType

logger = logging.getLogger(__name__)

# Median ≈ the "typical" run. Robust to the occasional very slow outlier, which
# a mean would let drag the estimate up.
_ESTIMATE_PERCENTILE = 0.5


class WorkflowDurationEstimate(BaseModel):
    """Estimated duration for a single workflow type."""

    type: WorkflowRunType
    estimated_seconds: float | None
    sample_size: int


class WorkflowDurationEstimatesResponse(BaseModel):
    """Duration estimates for every workflow type with historical data."""

    estimates: list[WorkflowDurationEstimate]


async def get_workflow_duration_estimates(
    project_id: str | None = None,
) -> WorkflowDurationEstimatesResponse:
    """Median run duration (seconds) and sample size per workflow type.

    Only COMPLETED runs are counted (CANCELLED / FAILED / timed-out runs would
    skew the estimate), and runs missing either timestamp are excluded. Always
    recomputes — callers on a hot path should cache the result.

    `project_id` is accepted but not yet used: the estimate is currently a
    global aggregate. It is part of the signature so the estimate can later be
    refined with project-specific characteristics (document size, reference
    count, etc.) without changing the API surface.
    """
    # Subtract two epoch extractions rather than the datetimes directly so the
    # expression stays plain numeric arithmetic (cleaner typing, same result).
    duration_seconds = func.extract(
        "epoch", col(WorkflowRun.completed_at)
    ) - func.extract("epoch", col(WorkflowRun.started_at))

    stmt = (
        select(
            col(WorkflowRun.type),
            func.percentile_cont(_ESTIMATE_PERCENTILE)
            .within_group(duration_seconds.asc())
            .label("estimate"),
            func.count().label("sample_size"),
        )
        .where(
            and_(
                col(WorkflowRun.status) == WorkflowRunStatus.COMPLETED,
                col(WorkflowRun.started_at).is_not(None),
                col(WorkflowRun.completed_at).is_not(None),
            )
        )
        .group_by(col(WorkflowRun.type))
    )

    async with get_async_db_session() as session:
        rows = (await session.execute(stmt)).all()

    estimates: list[WorkflowDurationEstimate] = []
    for row in rows:
        raw_type, estimate, sample_size = row[0], row[1], row[2]
        if estimate is None:
            continue
        try:
            workflow_type = WorkflowRunType(raw_type)
        except ValueError:
            # Deprecated/unknown type still present in old rows — skip it.
            continue
        estimates.append(
            WorkflowDurationEstimate(
                type=workflow_type,
                estimated_seconds=float(estimate),
                sample_size=int(sample_size),
            )
        )

    return WorkflowDurationEstimatesResponse(estimates=estimates)
