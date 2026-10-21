"""Integration tests for the per-project group_by_severity display setting.

A new project carries on the setting of the user's most recent own project, the
way the wizard pre-fills its assessments, and a PATCH changes it without
touching the project's other fields.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlmodel import col

from lib.config.database import get_async_db_session
from lib.models.project import Project
from lib.models.user import User, UserRole
from lib.services.projects.service import (
    UpdateProjectRequest,
    create_project,
    update_user_project,
)

BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)


class Seeder:
    """Creates users and projects and remembers them for teardown."""

    def __init__(self) -> None:
        self.user_ids: list[uuid.UUID] = []
        self.project_ids: list[uuid.UUID] = []

    async def user(self) -> User:
        user = User(
            id=uuid.uuid4(),
            email=f"group-by-severity-{uuid.uuid4()}@example.com",
            name="Group By Severity Tester",
            role=UserRole.USER,
            show_experimental_features=False,
        )
        async with get_async_db_session() as session:
            session.add(user)
            await session.commit()
        self.user_ids.append(user.id)
        return user

    async def project(
        self, user: User, *, age_days: int, group_by_severity: bool
    ) -> Project:
        project = Project(
            id=uuid.uuid4(),
            title=f"Project -{age_days}d",
            user_id=user.id,
            created_at=BASE_TIME - timedelta(days=age_days),
            group_by_severity=group_by_severity,
        )
        async with get_async_db_session() as session:
            session.add(project)
            await session.commit()
        self.project_ids.append(project.id)
        return project

    async def created(
        self, user: User, group_by_severity: bool | None = None
    ) -> Project:
        project = await create_project(
            title="New project", user=user, group_by_severity=group_by_severity
        )
        self.project_ids.append(project.id)
        return project

    async def cleanup(self) -> None:
        async with get_async_db_session() as session:
            await session.execute(
                delete(Project).where(col(Project.id).in_(self.project_ids))
            )
            await session.execute(delete(User).where(col(User.id).in_(self.user_ids)))
            await session.commit()


@pytest_asyncio.fixture
async def seeder():
    s = Seeder()
    yield s
    await s.cleanup()


@pytest.mark.asyncio
async def test_first_project_groups_by_severity(seeder):
    user = await seeder.user()

    project = await seeder.created(user)

    assert project.group_by_severity is True


@pytest.mark.asyncio
async def test_new_project_inherits_the_most_recent_projects_setting(seeder):
    user = await seeder.user()
    await seeder.project(user, age_days=10, group_by_severity=True)
    await seeder.project(user, age_days=1, group_by_severity=False)

    project = await seeder.created(user)

    assert project.group_by_severity is False


@pytest.mark.asyncio
async def test_other_users_projects_do_not_count(seeder):
    """Only the user's own projects count, so a project someone shared doesn't."""
    user = await seeder.user()
    other = await seeder.user()
    await seeder.project(user, age_days=10, group_by_severity=True)
    await seeder.project(other, age_days=1, group_by_severity=False)

    project = await seeder.created(user)

    assert project.group_by_severity is True


@pytest.mark.asyncio
async def test_an_explicit_value_wins_over_the_inherited_one(seeder):
    user = await seeder.user()
    await seeder.project(user, age_days=1, group_by_severity=False)

    project = await seeder.created(user, group_by_severity=True)

    assert project.group_by_severity is True


@pytest.mark.asyncio
async def test_patch_changes_the_setting_and_keeps_the_other_fields(seeder):
    user = await seeder.user()
    project = await seeder.created(user, group_by_severity=True)
    await update_user_project(
        str(project.id),
        UpdateProjectRequest(title="Titled", publication_date=date(2026, 3, 1)),
        user=user,
    )

    updated = await update_user_project(
        str(project.id), UpdateProjectRequest(group_by_severity=False), user=user
    )

    assert updated.group_by_severity is False
    assert updated.title == "Titled"
    assert updated.publication_date == date(2026, 3, 1)


@pytest.mark.asyncio
async def test_patch_with_a_null_date_still_clears_it(seeder):
    user = await seeder.user()
    project = await seeder.created(user)
    await update_user_project(
        str(project.id),
        UpdateProjectRequest(publication_date=date(2026, 3, 1)),
        user=user,
    )

    updated = await update_user_project(
        str(project.id), UpdateProjectRequest(publication_date=None), user=user
    )

    assert updated.publication_date is None
