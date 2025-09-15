import mimetypes
import os
from typing import List
from markitdown import MarkItDown
from pydantic import BaseModel


class FileDocument(BaseModel):
    file_name: str
    file_path: str
    file_type: str
    markdown: str


async def create_file_document_from_path(file_path: str) -> FileDocument:
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
    file_document = FileDocument(
        file_path=file_path,
        file_name=os.path.basename(file_path),
        file_type=mimetypes.guess_type(file_path)[0],
        markdown=markdown,
    )

    return file_document
