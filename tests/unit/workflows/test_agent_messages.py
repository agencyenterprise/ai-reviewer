import pytest
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from lib.workflows.abbreviation_scan_v2.chunk_models import AbbreviationChunk
from lib.workflows.abbreviation_scan_v2.state import AbbreviationScanV2State
from lib.workflows.about_this_ger.state import AgentConversation
from lib.workflows.claim_reference_validation_v2.state import SectionVerificationItem
from lib.workflows.reference_downloader.state import ReferenceFetchResult
from lib.workflows.reference_extraction.state import ReferenceExtractionState
from lib.workflows.reference_validation_v2.state import ReferenceValidationV2Item
from lib.workflows.reviewer_2.state import Reviewer2State
from lib.workflows.simple_deep_agent.state import SimpleDeepAgentState

MODELS_WITH_MESSAGES: list[type[BaseModel]] = [
    AgentConversation,
    AbbreviationChunk,
    AbbreviationScanV2State,
    SectionVerificationItem,
    ReferenceFetchResult,
    ReferenceExtractionState,
    ReferenceValidationV2Item,
    Reviewer2State,
    SimpleDeepAgentState,
]

# What a checkpointer-hydrated state can hold: a reducer appended a raw dict.
RAW_MESSAGE = {"type": "ai", "content": "already a dict"}


@pytest.mark.parametrize("model", MODELS_WITH_MESSAGES, ids=lambda m: m.__name__)
@pytest.mark.parametrize("mode", ["python", "json"])
def test_messages_dump_as_dicts_and_pass_raw_dicts_through(
    model: type[BaseModel], mode: str
) -> None:
    human = HumanMessage(content="hello")
    ai = AIMessage(content="hi")
    instance = model.model_construct(messages=[human, RAW_MESSAGE, ai])

    dumped = instance.model_dump(mode=mode, include={"messages"})["messages"]

    assert dumped[0] == human.model_dump(mode=mode)
    assert dumped[1] == RAW_MESSAGE
    assert dumped[2] == ai.model_dump(mode=mode)


@pytest.mark.parametrize("model", MODELS_WITH_MESSAGES, ids=lambda m: m.__name__)
def test_messages_serialization_schema_is_a_list_of_objects(
    model: type[BaseModel],
) -> None:
    schema = model.model_json_schema(mode="serialization")
    messages = schema["properties"]["messages"]

    assert messages["type"] == "array"
    assert messages["items"] == {"additionalProperties": True, "type": "object"}
