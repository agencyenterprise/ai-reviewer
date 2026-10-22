"""The initial state of the workflows that start from nothing but their config.

Most workflows leave every field but the type and the config at its default,
and take the base manifest's create_initial_state. The table pins which ones,
so a manifest that starts reading the database or dependency states is a
deliberate change.
"""

import pytest

from lib.workflows.models import BaseWorkflowConfig, WorkflowRunType
from lib.workflows.registry import get_all_manifests
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest

PROJECT_ID = "00000000-0000-0000-0000-000000000001"

# Workflows whose initial state is the config and the type, nothing else.
FRESH_STATE_TYPES = [
    WorkflowRunType.ABBREVIATION_SCAN_V2,
    WorkflowRunType.ABOUT_THIS_GER,
    WorkflowRunType.CLAIM_REFERENCE_VALIDATION_V2,
    WorkflowRunType.REFERENCE_VALIDATION_V2,
    WorkflowRunType.REVIEW_ASSISTANT,
] + [
    workflow_type
    for workflow_type, manifest in get_all_manifests().items()
    if isinstance(manifest, SimpleDeepAgentManifest)
]


def _config(workflow_type: WorkflowRunType) -> BaseWorkflowConfig:
    config_type = get_all_manifests()[workflow_type].get_config_type()
    return config_type(type=workflow_type, project_id=PROJECT_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize("workflow_type", FRESH_STATE_TYPES, ids=lambda t: t.value)
async def test_initial_state_is_the_config_and_type(
    workflow_type: WorkflowRunType,
) -> None:
    manifest = get_all_manifests()[workflow_type]
    config = _config(workflow_type)

    state = await manifest.create_initial_state(config, [], revision=1)

    assert state == manifest.get_state_type()(type=workflow_type, config=config)
