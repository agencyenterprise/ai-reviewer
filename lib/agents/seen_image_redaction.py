"""Keep viewed images out of a conversation's stored history once the model has seen them.

``view_image`` hands the model an image as base64 inside a ``ToolMessage``. A workflow
redacts those when it stores its transcript (``redact_image_blocks``), but a chat agent's
history lives in the checkpointer for the whole conversation: left there, every image
viewed would stay in it, megabytes each, and go back to the model on every later turn.

So after each model call, any image in a tool result that came before the model's new
response, which the model has therefore seen, is replaced by a short note. The image
the model is about to look at is never touched: it comes after the last response.
"""

from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langgraph.runtime import Runtime

from lib.agents.tools.view_image import redact_image_blocks


def _seen_with_images(messages: list[BaseMessage]) -> list[BaseMessage]:
    """The tool results before the newest response that still carry image bytes."""

    last_response = max(
        (i for i, message in enumerate(messages) if isinstance(message, AIMessage)),
        default=-1,
    )
    seen = [
        message
        for message in messages[:last_response]
        if isinstance(message, ToolMessage)
        and isinstance(message.content, list)
        and any(
            isinstance(block, dict) and block.get("type") == "image"
            for block in message.content
        )
    ]
    # Same ids, so the message reducer replaces them in place.
    return redact_image_blocks(seen)


class SeenImageRedactionMiddleware(AgentMiddleware[Any, Any, Any]):
    def after_model(self, state: Any, runtime: Runtime[Any]) -> dict[str, Any] | None:
        redacted = _seen_with_images(list(state.get("messages") or []))
        return {"messages": redacted} if redacted else None

    async def aafter_model(
        self, state: Any, runtime: Runtime[Any]
    ) -> dict[str, Any] | None:
        return self.after_model(state, runtime)
