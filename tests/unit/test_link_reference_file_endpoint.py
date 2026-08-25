"""Unit tests for the link-reference-file endpoint."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from lib.api.models import LinkReferenceFileRequest
from lib.models.file import FileRole
from lib.services.references import MatchSource

PROJECT_ID = str(uuid.uuid4())
REFERENCE_ID = str(uuid.uuid4())
FILE_ID = str(uuid.uuid4())


def _mock_user() -> MagicMock:
    user = MagicMock()
    user.id = str(uuid.uuid4())
    return user


def _mock_project(current_revision: int = 1) -> MagicMock:
    project = MagicMock()
    project.id = PROJECT_ID
    project.current_revision = current_revision
    return project


def _mock_file(file_id: str) -> MagicMock:
    file = MagicMock()
    file.id = file_id
    return file


def _patches(supporting_files: list, linked: bool):
    """Patch project access, the supporting-file lookup, and the link service."""
    return (
        patch(
            "lib.api.routers.projects.get_project_access",
            new=AsyncMock(return_value=(_mock_project(), None)),
        ),
        patch(
            "lib.api.routers.projects.get_files_by_project_id",
            new=AsyncMock(return_value=supporting_files),
        ),
        patch(
            "lib.api.routers.projects.add_file_to_reference",
            new=AsyncMock(return_value=linked),
        ),
    )


@pytest.mark.asyncio
async def test_links_supporting_file_to_reference():
    """Happy path returns the pair and records the match as MANUAL_UPLOAD."""
    from lib.api.routers.projects import link_reference_file_endpoint

    access, files, add = _patches([_mock_file(FILE_ID)], linked=True)
    with access, files, add as mock_add:
        result = await link_reference_file_endpoint(
            project_id=PROJECT_ID,
            reference_id=REFERENCE_ID,
            request=LinkReferenceFileRequest(file_id=FILE_ID),
            current_user=_mock_user(),
        )

    assert result.reference_id == REFERENCE_ID
    assert result.file_id == FILE_ID
    # A manual link must outrank whatever the automatic matcher decided.
    assert mock_add.call_args.kwargs["source"] is MatchSource.MANUAL_UPLOAD
    assert mock_add.call_args.kwargs["revision"] == 1


@pytest.mark.asyncio
async def test_only_supporting_files_are_considered():
    """The file lookup is scoped to SUPPORT files of the current revision."""
    from lib.api.routers.projects import link_reference_file_endpoint

    access, files, add = _patches([_mock_file(FILE_ID)], linked=True)
    with access, files as mock_files, add:
        await link_reference_file_endpoint(
            project_id=PROJECT_ID,
            reference_id=REFERENCE_ID,
            request=LinkReferenceFileRequest(file_id=FILE_ID),
            current_user=_mock_user(),
        )

    assert mock_files.call_args.kwargs["roles"] == [FileRole.SUPPORT]
    assert mock_files.call_args.kwargs["revision"] == 1


@pytest.mark.asyncio
async def test_file_from_another_project_raises_404():
    """A file_id that is not a supporting file of this project is rejected."""
    from lib.api.routers.projects import link_reference_file_endpoint

    # The project has a supporting file, but not the one being requested.
    access, files, add = _patches([_mock_file(str(uuid.uuid4()))], linked=True)
    with access, files, add as mock_add:
        with pytest.raises(HTTPException) as exc_info:
            await link_reference_file_endpoint(
                project_id=PROJECT_ID,
                reference_id=REFERENCE_ID,
                request=LinkReferenceFileRequest(file_id=FILE_ID),
                current_user=_mock_user(),
            )

    assert exc_info.value.status_code == 404
    # The link must not be attempted for a file we failed to validate.
    mock_add.assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_reference_raises_409():
    """add_file_to_reference returning False surfaces as a 409, not a success."""
    from lib.api.routers.projects import link_reference_file_endpoint

    access, files, add = _patches([_mock_file(FILE_ID)], linked=False)
    with access, files, add:
        with pytest.raises(HTTPException) as exc_info:
            await link_reference_file_endpoint(
                project_id=PROJECT_ID,
                reference_id=REFERENCE_ID,
                request=LinkReferenceFileRequest(file_id=FILE_ID),
                current_user=_mock_user(),
            )

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_relinking_the_same_reference_is_idempotent():
    """Posting twice links the same pair both times, never a second match.

    The replace semantics live in add_file_to_reference, which drops any
    existing match for the reference before adding the new one; this guards the
    endpoint against ever sending something that would append instead.
    """
    from lib.api.routers.projects import link_reference_file_endpoint

    access, files, add = _patches([_mock_file(FILE_ID)], linked=True)
    with access, files, add as mock_add:
        for _ in range(2):
            result = await link_reference_file_endpoint(
                project_id=PROJECT_ID,
                reference_id=REFERENCE_ID,
                request=LinkReferenceFileRequest(file_id=FILE_ID),
                current_user=_mock_user(),
            )
            assert result.file_id == FILE_ID

    assert mock_add.await_count == 2
    for call in mock_add.await_args_list:
        assert call.kwargs["reference_id"] == REFERENCE_ID
        assert call.kwargs["file_id"] == FILE_ID
