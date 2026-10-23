"""Finding a state class's run among a project's states, by the run type it pins."""

import pytest

from lib.workflows.models import WorkflowRunType
from lib.workflows.reference_extraction.state import (
    ReferenceExtractionConfig,
    ReferenceExtractionState,
)
from lib.workflows.reference_file_matching.state import (
    ReferenceFileMatchingConfig,
    ReferenceFileMatchingState,
)
from lib.workflows.simple_deep_agent.state import SimpleDeepAgentState
from lib.workflows.util import get_state_by_type, pinned_run_type


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

    found = get_state_by_type(ReferenceExtractionState, [_matching(), extraction])

    assert found is extraction


def test_returns_none_when_no_state_has_the_run_type() -> None:
    found = get_state_by_type(ReferenceExtractionState, [_matching()])

    assert found is None


def test_a_state_class_pins_its_run_type_with_its_literal() -> None:
    assert (
        pinned_run_type(ReferenceExtractionState)
        == WorkflowRunType.REFERENCE_EXTRACTION
    )


def test_a_state_shared_across_run_types_pins_none() -> None:
    assert pinned_run_type(SimpleDeepAgentState) is None


def test_looking_up_a_state_shared_across_run_types_raises() -> None:
    with pytest.raises(TypeError, match="SimpleDeepAgentState"):
        get_state_by_type(SimpleDeepAgentState, [_extraction()])
