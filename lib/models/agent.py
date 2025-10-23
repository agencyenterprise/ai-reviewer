import logging
from typing import Any, Protocol, runtime_checkable

from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_LLM_TIMEOUT = 300


@runtime_checkable
class AgentProtocol(Protocol):
    name: str
    description: str

    async def ainvoke(
        self, prompt_kwargs: dict, config: RunnableConfig = None
    ) -> Any: ...


class QCResult(BaseModel):
    valid: bool
    feedback: str
