import mimetypes
import os
from typing import List
from markitdown import MarkItDown
from pydantic import BaseModel, Field


class FileDocument(BaseModel):
    file_name: str = Field(default="untitled", alias="fileName")
    file_path: str = Field(default="/tmp/temp", alias="filePath") 
    file_type: str = Field(default="text/markdown", alias="fileType")
    markdown: str
    
    model_config = {"populate_by_name": True}


async def create_file_document_from_path(file_path: str) -> FileDocument:
    # Verify file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    # Convert content to markdown
    md = MarkItDown(enable_plugins=False)  # Set to True to enable plugins
    result = md.convert(file_path)
    markdown = result.markdown

    # TODO: For PDFs, we may need something like this:
    # result = await markdown_cleaner_agent.apply(
    #     prompt_kwargs={
    #         "full_document": result.markdown,
    #     }
    # )
    # self._markdown = result.text

    # Create File object for main document
    # Handle case where mimetypes.guess_type returns None
    file_type = mimetypes.guess_type(file_path)[0] or "text/plain"
    
    file_document = FileDocument(
        file_path=str(file_path),
        file_name=os.path.basename(file_path),
        file_type=file_type,
        markdown=markdown,
    )
    
    return file_document
