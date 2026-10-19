"""Images the model has seen leave a conversation's stored history."""

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from lib.agents.seen_image_redaction import SeenImageRedactionMiddleware

# The hook reads only the state.
RUNTIME = MagicMock()

IMAGE = {
    "type": "image",
    "source_type": "base64",
    "data": "AAAA" * 100,
    "mime_type": "image/png",
}


def history(*after_the_look: AIMessage) -> list:
    return [
        HumanMessage(content="What does Figure 3 show?", id="h1"),
        AIMessage(
            content="",
            id="a1",
            tool_calls=[
                {"id": "c1", "name": "view_image", "args": {"image_reference": "x"}}
            ],
        ),
        ToolMessage(content=[IMAGE], tool_call_id="c1", id="t1"),
        *after_the_look,
    ]


def test_an_image_the_model_has_answered_about_is_replaced_by_a_note() -> None:
    update = SeenImageRedactionMiddleware().after_model(
        {"messages": history(AIMessage(content="A radar chart.", id="a2"))}, RUNTIME
    )

    assert update is not None
    (redacted,) = update["messages"]
    assert redacted.id == "t1", "same id, so it replaces the stored one"
    assert (
        redacted.content[0]["type"] == "text"
        and "bytes omitted" in redacted.content[0]["text"]
    )


def test_an_image_the_model_is_about_to_see_is_left_alone() -> None:
    """It comes after the last response: the next model call needs its bytes."""

    assert (
        SeenImageRedactionMiddleware().after_model({"messages": history()}, RUNTIME)
        is None
    )
