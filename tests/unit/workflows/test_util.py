"""Finding one workflow run type's state among a project's states."""

import pytest

from lib.workflows.document_processing.state import DocumentProcessingState
from lib.workflows.models import WorkflowRunType
from lib.workflows.reference_extraction.state import (
    ReferenceExtractionConfig,
    ReferenceExtractionState,
)
from lib.workflows.reference_file_matching.state import (
    ReferenceFileMatchingConfig,
    ReferenceFileMatchingState,
)
from lib.workflows.util import get_state_by_type


def _extraction() -> ReferenceExtractionState:
    return ReferenceExtractionState(
        config=ReferenceExtractionConfig(project_id="p"), file_id="main"
    )


def _matching() -> ReferenceFileMatchingState:
    return ReferenceFileMatchingState(
        config=ReferenceFileMatchingConfig(project_id="p"), file_id="main"
    )


def test_returns_the_state_of_the_run_type() -> None:
    extraction = _extraction()

    found = get_state_by_type(
        WorkflowRunType.REFERENCE_EXTRACTION,
        ReferenceExtractionState,
        [_matching(), extraction],
    )

    assert found is extraction


def test_returns_none_when_no_state_has_the_run_type() -> None:
    found = get_state_by_type(
        WorkflowRunType.REFERENCE_EXTRACTION, ReferenceExtractionState, [_matching()]
    )

    assert found is None


def test_naming_the_wrong_state_class_raises() -> None:
    with pytest.raises(TypeError, match="DocumentProcessingState"):
        get_state_by_type(
            WorkflowRunType.REFERENCE_EXTRACTION,
            DocumentProcessingState,
            [_extraction()],
        )
