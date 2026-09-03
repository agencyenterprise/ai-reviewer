import logging

import aiofiles
from langchain.tools import ToolRuntime, tool

from lib.services.converters.markitdown import markitdown_converter
from lib.services.files import get_file_by_id
from lib.workflows.context import ContextSchema

logger = logging.getLogger(__name__)

MAX_CONTENT_CHARS = 4000


@tool()
async def read_file_content(file_id: str, runtime: ToolRuntime[ContextSchema]):
    """
    Read the content of a file by its ID. Returns the content of the file in markdown format. Truncates the content to the first 4000 characters.

    Args:
        file_id: The ID of the file to read the content from.

    Returns:
        The first 4000 characters of the content of the file in markdown format.
    """

    return await _read_file_content_async(file_id)


async def _read_file_content_async(file_id: str) -> str | None:
    file = await get_file_by_id(file_id)
    if file is None:
        logger.warning("read_file_content: no file record for id %s", file_id)
        return None

    if file.file_type == "text/markdown":
        # If file is already markdown, read directly from disk, no need to convert
        content = await _read_file_directly(file.file_path)
    else:
        # Use markitdown for conversion of non-markdown files
        content = await markitdown_converter.convert_to_markdown(file.file_path)

    total_chars = len(content) if content else 0
    if total_chars == 0:
        logger.warning(
            "read_file_content: file %s (%s, %s) produced no text",
            file_id,
            file.file_type,
            file.file_path,
        )
        return None

    logger.info(
        "read_file_content: file %s (%s) has %d chars, returning first %d",
        file_id,
        file.file_type,
        total_chars,
        min(total_chars, MAX_CONTENT_CHARS),
    )
    return content[:MAX_CONTENT_CHARS]


async def _read_file_directly(file_path: str) -> str:
    """Read file content directly from disk."""

    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        return await f.read()
