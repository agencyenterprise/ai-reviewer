"""Each MCP tool that takes a project_id asks `get_project_access` for the level it needs.

The tool unit tests mock the access check away, so only these tests notice a
write tool that stops asking for WRITE. The read-only caller is an admin on a
project whose feedback visibility is full_project: the one way an MCP user
(who never carries a share token) gets READ without WRITE.

`get_workflow_run` takes a run id instead; test_mcp_project_reads.py checks
that it refuses strangers.
"""

import json
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlmodel import col

from lib.api.mcp.tools.files import (
    export_project_docx,
    list_project_files,
    remove_reference_file,
)
from lib.api.mcp.tools.projects import get_project, get_project_references
from lib.api.mcp.tools.revisions import create_revision, list_revisions
from lib.api.mcp.tools.uploads import get_tus_upload_credentials
from lib.api.mcp.tools.workflows import run_workflow
from lib.config.database import get_async_db_session
from lib.models.project import FeedbackVisibility, Project
from lib.models.user import User, UserRole

ToolCall = Callable[[str], Awaitable[Any]]

WRITE_TOOLS: dict[str, ToolCall] = {
    "create_revision": lambda pid: create_revision(pid, token=MagicMock()),
    "get_tus_upload_credentials": lambda pid: get_tus_upload_credentials(
        pid, token=MagicMock()
    ),
    "remove_reference_file": lambda pid: remove_reference_file(
        pid, str(uuid.uuid4()), token=MagicMock()
    ),
    "run_workflow": lambda pid: run_workflow(
        pid, ["recommendation_check"], ctx=MagicMock(), token=MagicMock()
    ),
}

READ_TOOLS: dict[str, ToolCall] = {
    "export_project_docx": lambda pid: export_project_docx(pid, token=MagicMock()),
    "get_project": lambda pid: get_project(pid, token=MagicMock()),
    "get_project_references": lambda pid: get_project_references(
        pid, token=MagicMock()
    ),
    "list_project_files": lambda pid: list_project_files(pid, token=MagicMock()),
    "list_revisions": lambda pid: list_revisions(pid, token=MagicMock()),
}


def _user(label: str, role: UserRole) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"mcp-access-{label}-{uuid.uuid4()}@example.com",
        name=label,
        role=role,
        show_experimental_features=False,
    )


@pytest_asyncio.fixture
async def shared(tmp_path: Path) -> AsyncIterator[dict[str, Any]]:
    """A project the admin may read but not write, and a stranger may not see."""
    owner = _user("owner", UserRole.USER)
    admin = _user("admin", UserRole.ADMIN)
    stranger = _user("stranger", UserRole.USER)
    project = Project(
        id=uuid.uuid4(),
        title="MCP access",
        user_id=owner.id,
        feedback_visibility=FeedbackVisibility.FULL_PROJECT,
    )
    async with get_async_db_session() as session:
        session.add_all([owner, admin, stranger])
        await session.flush()
        session.add(project)
        await session.commit()

    docx = tmp_path / "reviewed.docx"
    docx.write_bytes(b"docx")
    # No tool below may start a workflow or build a real export.
    runner = AsyncMock()
    with (
        patch("lib.api.mcp.helpers.require_api_key"),
        patch("lib.api.mcp.tools.workflows.run_multiple_workflows_blocking", runner),
        patch(
            "lib.api.mcp.tools.files.generate_docx",
            new=AsyncMock(return_value=(str(docx), "reviewed.docx")),
        ),
    ):
        yield {
            "project_id": str(project.id),
            "owner": owner,
            "admin": admin,
            "stranger": stranger,
            "runner": runner,
        }

    async with get_async_db_session() as session:
        await session.execute(delete(Project).where(col(Project.id) == project.id))
        await session.execute(
            delete(User).where(col(User.id).in_([owner.id, admin.id, stranger.id]))
        )
        await session.commit()


async def _call_as(user: User, tool: ToolCall, project_id: str) -> Any:
    with patch("lib.api.mcp.helpers.resolve_user", new=AsyncMock(return_value=user)):
        return await tool(project_id)


async def _current_revision(project_id: str) -> int:
    async with get_async_db_session() as session:
        return (
            await session.execute(
                select(col(Project.current_revision)).where(
                    col(Project.id) == uuid.UUID(project_id)
                )
            )
        ).scalar_one()


@pytest.mark.asyncio
@pytest.mark.parametrize("name", sorted(WRITE_TOOLS))
async def test_write_tools_refuse_a_reader(shared: dict[str, Any], name: str) -> None:
    with pytest.raises(HTTPException) as exc:
        await _call_as(shared["admin"], WRITE_TOOLS[name], shared["project_id"])

    assert exc.value.status_code == 403
    assert exc.value.detail == "Write access required"
    shared["runner"].assert_not_called()
    assert await _current_revision(shared["project_id"]) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("name", sorted(WRITE_TOOLS | READ_TOOLS))
async def test_project_tools_refuse_a_stranger(
    shared: dict[str, Any], name: str
) -> None:
    tool = (WRITE_TOOLS | READ_TOOLS)[name]
    with pytest.raises(HTTPException) as exc:
        await _call_as(shared["stranger"], tool, shared["project_id"])

    assert exc.value.status_code == 403
    assert exc.value.detail == "Access denied"
    shared["runner"].assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("name", sorted(READ_TOOLS))
async def test_read_tools_serve_a_reader(shared: dict[str, Any], name: str) -> None:
    result = await _call_as(shared["admin"], READ_TOOLS[name], shared["project_id"])

    assert result is not None


@pytest.mark.asyncio
async def test_the_owner_may_write(shared: dict[str, Any]) -> None:
    """The control for the refusals above: the same call works for the owner."""
    data = json.loads(
        await _call_as(
            shared["owner"],
            WRITE_TOOLS["get_tus_upload_credentials"],
            shared["project_id"],
        )
    )

    assert data["required_metadata"]["project_id"] == shared["project_id"]
