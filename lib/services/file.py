import logging
import mimetypes
import os
from typing import List
from markitdown import MarkItDown
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FileDocument(BaseModel):
    file_name: str = Field(default="untitled", alias="fileName")
    file_path: str = Field(default="/tmp/temp", alias="filePath") 
    file_type: str = Field(default="text/markdown", alias="fileType")
    markdown: str
    
    model_config = {"populate_by_name": True}


async def create_file_document_from_path(file_path: str) -> FileDocument:
    logger.info(f"Processing file: {file_path}")
    
    # Verify file exists and get basic info
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    file_size = os.path.getsize(file_path)
    logger.info(f"File size: {file_size} bytes")
    
    # Convert content to markdown
    md = MarkItDown(enable_plugins=False)  # Set to True to enable plugins
    logger.info("Converting file to markdown...")
    result = md.convert(file_path)
    markdown = result.markdown
    logger.info(f"Markdown conversion complete: {len(markdown)} characters")

    # TODO: For PDFs, we may need something like this:
    # result = await markdown_cleaner_agent.apply(
    #     prompt_kwargs={
    #         "full_document": result.markdown,
    #     }
    # )
    # self._markdown = result.text

    # Create File object for main document
    # Handle case where mimetypes.guess_type returns None
    mime_result = mimetypes.guess_type(file_path)
    logger.info(f"mimetypes.guess_type({file_path}) returned: {mime_result}")
    
    file_type = mime_result[0] or "text/plain"
    logger.info(f"Using file_type: {file_type}")
    
    file_name = os.path.basename(file_path)
    logger.info(f"Using file_name: {file_name}")
    
    file_document = FileDocument(
        file_path=str(file_path),
        file_name=file_name,
        file_type=file_type,
        markdown=markdown,
    )
    
    logger.info(f"FileDocument created successfully: {file_document.file_name}, {file_document.file_type}")
    return file_document
