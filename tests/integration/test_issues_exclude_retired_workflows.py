"""Issues from retired workflows must not be returned.

Issues outlive the workflow that produced them: the row keeps whatever
`workflow_type` string was current when it was written, and nothing deletes it
when a workflow is removed. Before this filter a project kept surfacing findings
from workflows that no longer exist — with no run to open, and labelled with the
raw type slug, because the display name only resolves through a manifest.
"""

import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlmodel import col

from lib.config.database import get_async_db_session
from lib.models.issue import Issue, IssueStatus
from lib.models.project import Project
from lib.models.workflow_run import WorkflowRun, WorkflowRunStatus
from lib.models.user import User, UserRole
from lib.services.issue_persistence import get_project_issues
from lib.workflows.models import SeverityEnum, WorkflowRunType

# A type string that used to exist and still sits in real rows, but is no longer
# a WorkflowRunType member at all.
RETIRED_TYPE = "claim_substantiation"
LIVE_TYPE = WorkflowRunType.RECOMMENDATION_CHECK


@pytest_asyncio.fixture
async def project_with_mixed_issues():
    user = User(
        id=uuid.uuid4(),
        email=f"retired-wf-{uuid.uuid4()}@example.com",
        name="Test User",
        role=UserRole.USER,
        show_experimental_features=False,
    )
    project = Project(
        id=uuid.uuid4(), user_id=user.id, current_revision=1, title="retired-wf test"
    )

    runs = {
        t: WorkflowRun(
            id=uuid.uuid4(),
            project_id=project.id,
            type=t,  # type: ignore[arg-type]  # raw string is exactly the retired-row case
            langgraph_thread_id=str(uuid.uuid4()),
            status=WorkflowRunStatus.COMPLETED,
            revision=1,
        )
        for t in (RETIRED_TYPE, LIVE_TYPE.value)
    }

    def _issue(workflow_type: str, title: str) -> Issue:
        now = datetime.now(UTC)
        return Issue(
            id=uuid.uuid4(),
            project_id=project.id,
            workflow_run_id=runs[workflow_type].id,
            issue_hash=str(uuid.uuid4()),
            revision=1,
            title=title,
            description="d",
            severity=SeverityEnum.LOW,
            workflow_type=workflow_type,  # type: ignore[arg-type]  # raw string is exactly the retired-row case
            status=IssueStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    async with get_async_db_session() as session:
        session.add(user)
        await session.commit()

    async with get_async_db_session() as session:
        session.add(project)
        await session.commit()

    async with get_async_db_session() as session:
        for run in runs.values():
            session.add(run)
        await session.commit()

    async with get_async_db_session() as session:
        session.add(_issue(RETIRED_TYPE, "from a retired workflow"))
        session.add(_issue(LIVE_TYPE.value, "from a live workflow"))
        await session.commit()

    yield project

    async with get_async_db_session() as session:
        await session.execute(delete(Issue).where(col(Issue.project_id) == project.id))
        await session.execute(
            delete(WorkflowRun).where(col(WorkflowRun.project_id) == project.id)
        )
        await session.execute(delete(Project).where(col(Project.id) == project.id))
        await session.execute(delete(User).where(col(User.id) == user.id))
        await session.commit()


@pytest.mark.asyncio
async def test_issues_from_retired_workflows_are_not_returned(project_with_mixed_issues):
    issues = await get_project_issues(project_with_mixed_issues.id, revision=1)

    titles = {i.title for i in issues}
    assert titles == {"from a live workflow"}
    assert all(str(i.workflow_type) != RETIRED_TYPE for i in issues)


@pytest.mark.asyncio
async def test_the_retired_issue_row_still_exists(project_with_mixed_issues):
    """Filtered from the API, not deleted — the row stays recoverable."""
    async with get_async_db_session() as session:
        stmt = select(Issue).where(
            col(Issue.project_id) == project_with_mixed_issues.id,
            col(Issue.workflow_type) == RETIRED_TYPE,
        )
        assert (await session.execute(stmt)).scalar_one_or_none() is not None
