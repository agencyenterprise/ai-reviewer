"""The state and config types each manifest hands out.

Run state is hydrated, and a run's config built, from these types, so a
manifest that answers with the wrong one breaks every stored run of its
workflow. The table pins what each registered manifest answers.
"""

from typing import get_args

import pytest
from langgraph.graph import StateGraph

from lib.workflows.abbreviation_scan_v2.state import (
    AbbreviationScanV2Config,
    AbbreviationScanV2State,
)
from lib.workflows.about_this_ger.state import AboutThisGerConfig, AboutThisGerState
from lib.workflows.claim_reference_validation_v2.state import (
    ClaimReferenceValidationV2Config,
    ClaimReferenceValidationV2State,
)
from lib.workflows.document_processing.state import (
    DocumentProcessingState,
    DocumentProcessingWorkflowConfig,
)
from lib.workflows.document_summarization.state import (
    DocumentSummarizationState,
    DocumentSummarizationWorkflowConfig,
)
from lib.workflows.manifest import WorkflowManifest
from lib.workflows.models import (
    BaseWorkflowConfig,
    BaseWorkflowState,
    DocumentIssue,
    WorkflowRunType,
)
from lib.workflows.reference_downloader.state import (
    ReferenceDownloaderState,
    ReferenceDownloaderWorkflowConfig,
)
from lib.workflows.reference_extraction.state import (
    ReferenceExtractionConfig,
    ReferenceExtractionState,
)
from lib.workflows.reference_file_matching.state import (
    ReferenceFileMatchingConfig,
    ReferenceFileMatchingState,
)
from lib.workflows.reference_validation_v2.state import (
    ReferenceValidationV2State,
    ReferenceValidationV2WorkflowConfig,
)
from lib.workflows.registry import get_all_manifests, register_workflow_manifest
from lib.workflows.review_assistant.state import (
    ReviewAssistantConfig,
    ReviewAssistantState,
)
from lib.workflows.reviewer_2.state import Reviewer2Config, Reviewer2State
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest
from lib.workflows.simple_deep_agent.state import (
    SimpleDeepAgentConfig,
    SimpleDeepAgentState,
)
from lib.workflows.workflow_types import WorkflowState

# Workflows with a state of their own; every other one is a simple deep agent.
OWN_TYPES: dict[
    WorkflowRunType, tuple[type[BaseWorkflowState], type[BaseWorkflowConfig]]
] = {
    WorkflowRunType.ABBREVIATION_SCAN_V2: (
        AbbreviationScanV2State,
        AbbreviationScanV2Config,
    ),
    WorkflowRunType.ABOUT_THIS_GER: (AboutThisGerState, AboutThisGerConfig),
    WorkflowRunType.CLAIM_REFERENCE_VALIDATION_V2: (
        ClaimReferenceValidationV2State,
        ClaimReferenceValidationV2Config,
    ),
    WorkflowRunType.DOCUMENT_PROCESSING: (
        DocumentProcessingState,
        DocumentProcessingWorkflowConfig,
    ),
    WorkflowRunType.DOCUMENT_SUMMARIZATION: (
        DocumentSummarizationState,
        DocumentSummarizationWorkflowConfig,
    ),
    WorkflowRunType.REFERENCE_DOWNLOADER: (
        ReferenceDownloaderState,
        ReferenceDownloaderWorkflowConfig,
    ),
    WorkflowRunType.REFERENCE_EXTRACTION: (
        ReferenceExtractionState,
        ReferenceExtractionConfig,
    ),
    WorkflowRunType.REFERENCE_FILE_MATCHING: (
        ReferenceFileMatchingState,
        ReferenceFileMatchingConfig,
    ),
    WorkflowRunType.REFERENCE_VALIDATION_V2: (
        ReferenceValidationV2State,
        ReferenceValidationV2WorkflowConfig,
    ),
    WorkflowRunType.REVIEW_ASSISTANT: (ReviewAssistantState, ReviewAssistantConfig),
    WorkflowRunType.REVIEWER_2: (Reviewer2State, Reviewer2Config),
}

SIMPLE_TYPES = (SimpleDeepAgentState, SimpleDeepAgentConfig)


@pytest.mark.parametrize(
    "workflow_type", list(get_all_manifests()), ids=lambda t: t.value
)
def test_manifest_answers_with_its_state_and_config_types(
    workflow_type: WorkflowRunType,
) -> None:
    manifest = get_all_manifests()[workflow_type]

    expected = OWN_TYPES.get(workflow_type, SIMPLE_TYPES)

    assert (manifest.get_state_type(), manifest.get_config_type()) == expected


def test_registering_a_manifest_without_type_arguments_fails() -> None:
    class Untyped(SimpleDeepAgentManifest):
        type = WorkflowRunType.DOCUMENT_STRUCTURE

    # Simulates a manifest that never named [State, Config].
    Untyped._state_type = None

    with pytest.raises(TypeError, match="Untyped"):
        register_workflow_manifest(Untyped())


@pytest.mark.parametrize("workflow_type", list(OWN_TYPES), ids=lambda t: t.value)
def test_own_state_manifest_takes_its_type_from_the_state_literal(
    workflow_type: WorkflowRunType,
) -> None:
    state_type, _ = OWN_TYPES[workflow_type]

    assert get_args(state_type.model_fields["type"].annotation) == (workflow_type,)
    assert get_all_manifests()[workflow_type].type == workflow_type


def test_declaring_a_type_the_state_literal_sets_fails() -> None:
    with pytest.raises(TypeError, match="Reviewer2State already sets"):

        class Declared(WorkflowManifest[Reviewer2State, Reviewer2Config]):
            type = WorkflowRunType.REVIEWER_2

            def build_graph(self) -> StateGraph:
                raise NotImplementedError

            def convert_state_to_issues(
                self, state: Reviewer2State, other_states: list[WorkflowState]
            ) -> list[DocumentIssue]:
                return []
