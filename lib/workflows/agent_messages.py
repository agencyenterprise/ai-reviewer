from typing import Annotated

from langchain_core.messages import BaseMessage
from pydantic import PlainSerializer


def _dump_messages(messages: list[BaseMessage]) -> list[dict]:
    # Checkpointer-hydrated states may contain raw dicts in `messages`
    # because reducers can append items that bypass model construction.
    return [m if isinstance(m, dict) else m.model_dump() for m in messages]


AgentMessages = Annotated[list[BaseMessage], PlainSerializer(_dump_messages)]
"""An agent's LLM conversation, as a state field: dumps each message as a dict."""
