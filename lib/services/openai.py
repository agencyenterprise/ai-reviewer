import logging
from asyncio import sleep
from time import monotonic
from typing import TypeVar

from langfuse.openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types.responses import ParsedResponse
from pydantic import BaseModel

from lib.config.env import config
from lib.models.agent import DEFAULT_LLM_TIMEOUT

logger = logging.getLogger(__name__)


ResponseFormatT = TypeVar("ResponseFormatT")


def get_openai_client() -> AsyncOpenAI:
    if config.AZURE_OPENAI_API_KEY and config.AZURE_OPENAI_ENDPOINT:
        return AsyncAzureOpenAI(timeout=DEFAULT_LLM_TIMEOUT)
    else:
        return AsyncOpenAI(timeout=DEFAULT_LLM_TIMEOUT)


async def wait_for_response(
    client: AsyncOpenAI,
    response: ParsedResponse[ResponseFormatT],
    poll_interval_seconds: int = 5,
) -> ParsedResponse[ResponseFormatT]:
    start_time = monotonic()

    while response.status in {"queued", "in_progress"}:
        await sleep(poll_interval_seconds)
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
