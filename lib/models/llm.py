from abc import abstractmethod
from typing import Any
from langfuse.openai import AsyncOpenAI
from pydantic import BaseModel
from lib.models.react_agent.agent_runner import _ensure_structured_output
from time import sleep

import logging

logger = logging.getLogger(__name__)


class LLMClient(BaseModel):
    provider: str
    model: str

    tools: list[dict]
    background: bool = False  # Is background model?
    output_schema: Any

    @abstractmethod
    async def ainvoke(self, input: str) -> str:
        pass


class OpenAIWrapper(LLMClient):
    provider: str = "openai"
    client: Any | None = None
    status: str | None = None
    resp: Any | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = AsyncOpenAI()

    async def ainvoke(self, input: str) -> str:

        input_dict = [
            message.model_dump(include={"content", "type", "role"}) for message in input
        ]
        for message in input_dict:
            if message.get("type"):
                message["role"] = message["type"]
                del message["type"]
            if message.get("role") == "human":
                message["role"] = "user"

        structured_output = (
            self.output_schema is not None and self.output_schema is not str
        )
        if not structured_output:
            self.resp = await self.client.responses.create(
                model=self.model,
                input=input_dict,
                background=self.background,
                tools=self.tools,
            )
        else:
            self.resp = await self.client.responses.parse(
                model=self.model,
                input=input_dict,
                background=self.background,
                tools=self.tools,
                text_format=self.output_schema,
            )

        # Store the original response before polling
        original_resp = self.resp

        if not self.background:
            return (
                self.resp.output_text
                if not structured_output
                else self.resp.output_parsed
            )
        else:
            logger.info(
                "Calling %s in background mode and waiting for response", self.model
            )
            while self.resp.status in {"queued", "in_progress"}:
                self.status = self.resp.status
                sleep(2)
                self.resp = await self.client.responses.retrieve(original_resp.id)
                logger.info(
                    "Call id: %s => Current status: %s... Checking back in 2 seconds",
                    self.resp.id,
                    self.resp.status,
                )
            self.status = self.resp.status
            return (
                self.resp.output_text
                if not structured_output
                else _ensure_structured_output(
                    self.resp.output_text, self.output_schema
                )
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.background and hasattr(self, "resp") and hasattr(self, "client"):
            try:
                self.client.responses.cancel(self.resp.id)
            except Exception as e:
                logger.error("Error canceling response: %s", e)
            self.client.close()
