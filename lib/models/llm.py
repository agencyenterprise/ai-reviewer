from abc import abstractmethod
from typing import Any, TypeVar
from langfuse.openai import AsyncOpenAI
from openai.types.responses import ParsedResponse
from pydantic import BaseModel
from lib.models.react_agent.agent_runner import ensure_structured_output
from time import sleep, monotonic

import logging

logger = logging.getLogger(__name__)


async def coerce_to_schema(text: str, schema: Any) -> Any:
    """Attempt to coerce text into the given schema using a parsing model."""
    coerce_prompt = [
        {
            "role": "system",
            "content": "Convert the following text into a JSON object that strictly matches the provided JSON Schema. Output only JSON.",
        },
        {
            "role": "user",
            "content": f"JSON Schema:\n{schema.model_json_schema()}",
        },
        {"role": "user", "content": f"Text:\n{text}"},
    ]
    try:
        coercion = await AsyncOpenAI().responses.parse(
            model="gpt-5",  # or a lightweight model you know supports parse
            input=coerce_prompt,
            text_format=schema,
        )
        return coercion.output_parsed
    except Exception:
        logger.warning("Secondary schema coercion failed; returning raw text")
        return text


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
        used_parse = False
        if not structured_output:
            self.resp = await self.client.responses.create(
                model=self.model,
                input=input_dict,
                background=self.background,
                tools=self.tools,
            )
        else:
            # Attempt structured parsing; if unsupported by the model, fall back to create
            try:
                self.resp = await self.client.responses.parse(
                    model=self.model,
                    input=input_dict,
                    background=self.background,
                    tools=self.tools,
                    text_format=self.output_schema,
                )
                used_parse = True
            except Exception as e:
                logger.warning(
                    "Structured parse not supported for model %s; falling back to create. Error: %s",
                    self.model,
                    getattr(e, "message", str(e)),
                )
                self.resp = await self.client.responses.create(
                    model=self.model,
                    input=input_dict,
                    background=self.background,
                    tools=self.tools,
                )

        # Store the original response before polling
        original_resp = self.resp

        if not self.background:
            if not structured_output:
                return self.resp.output_text
            if used_parse and hasattr(self.resp, "output_parsed"):
                return self.resp.output_parsed
            try:
                return ensure_structured_output(
                    self.resp.output_text, self.output_schema
                )
            except Exception as e:
                logger.warning("Error parsing structured output: %s", e)
                return await coerce_to_schema(self.resp.output_text, self.output_schema)
        else:
            logger.info(
                "Calling %s in background mode and waiting for response", self.model
            )
            while self.resp.status in {"queued", "in_progress"}:
                self.status = self.resp.status
                sleep(5)
                self.resp = await self.client.responses.retrieve(original_resp.id)
                logger.info(
                    "Call id: %s => Current status: %s... Checking back in 5 seconds",
                    self.resp.id,
                    self.resp.status,
                )
            self.status = self.resp.status

            if not structured_output:
                return self.resp.output_text
            if used_parse and hasattr(self.resp, "output_parsed"):
                return self.resp.output_parsed
            try:
                return ensure_structured_output(
                    self.resp.output_text, self.output_schema
                )
            except Exception as e:
                logger.warning("Error parsing structured output: %s", e)
                return await coerce_to_schema(self.resp.output_text, self.output_schema)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.background and hasattr(self, "resp") and hasattr(self, "client"):
            try:
                self.client.responses.cancel(self.resp.id)
            except Exception as e:
                logger.error("Error canceling response: %s", e)
            self.client.close()


ResponseFormatT = TypeVar("ResponseFormatT")


async def wait_for_response(
    client: AsyncOpenAI,
    response: ParsedResponse[ResponseFormatT],
    poll_interval_seconds: int = 5,
) -> ParsedResponse[ResponseFormatT]:
    start_time = monotonic()

    while response.status in {"queued", "in_progress"}:
        sleep(poll_interval_seconds)
        response = await client.responses.retrieve(response.id)
        elapsed = monotonic() - start_time
        logger.info(
            "Call id: %s => Current status: %s... Running for %.1fs. Checking back in %s seconds",
            response.id,
            response.status,
            elapsed,
            poll_interval_seconds,
        )

    return response


def ensure_structured_output_response(
    response: ParsedResponse[ResponseFormatT], schema: type[BaseModel]
) -> BaseModel:
    """Validate or coerce the output into the expected Pydantic model.

    If the output is already a dict, validate directly. If it's a string, let the
    schema try to parse JSON. As a last resort, raise and let caller decide fallback.
    """
    if hasattr(response, "output_parsed") and isinstance(
        response.output_parsed, BaseModel
    ):
        return response.output_parsed

    if hasattr(response, "output_text") and isinstance(response.output_text, str):
        return schema.model_validate_json(response.output_text)

    raise ValueError("Response did not include a structured result.")
