"""Unit tests for ReferenceDownloaderManifest.create_initial_state seeding.

reference_downloader is the one accumulating workflow: it carries fetched
references across runs. Since runs no longer share a langgraph_thread_id, the
prior run's results are handed in via prior_self_state instead of the
checkpointer — these tests pin that seeding behavior.
"""

import uuid

import pytest

from lib.workflows.models import WorkflowRunType
from lib.workflows.reference_downloader.manifest import ReferenceDownloaderManifest
from lib.workflows.reference_downloader.state import (
    ReferenceDownloaderState,
    ReferenceDownloaderWorkflowConfig,
    ReferenceFetchResult,
    ReferenceFetchStatus,
)


def _config() -> ReferenceDownloaderWorkflowConfig:
    return ReferenceDownloaderWorkflowConfig(
        type=WorkflowRunType.REFERENCE_DOWNLOADER,
        project_id=str(uuid.uuid4()),
        references=[],
    )


@pytest.mark.asyncio
async def test_create_initial_state_seeds_fetched_references_from_prior():
    """The new run carries forward the prior run's fetched_references."""
    config = _config()
    prior = ReferenceDownloaderState(
        type=WorkflowRunType.REFERENCE_DOWNLOADER,
        config=config,
        fetched_references=[
            ReferenceFetchResult(
                reference_id="r1",
                input_reference="ref 1",
                status=ReferenceFetchStatus.COMPLETED,
            )
        ],
    )

    state = await ReferenceDownloaderManifest().create_initial_state(
        config, [], 1, prior_self_state=prior
    )

    assert [r.reference_id for r in state.fetched_references] == ["r1"]


@pytest.mark.asyncio
async def test_create_initial_state_empty_without_prior():
    """A first run (no prior state) starts with no fetched_references."""
    state = await ReferenceDownloaderManifest().create_initial_state(_config(), [], 1)

    assert state.fetched_references == []
