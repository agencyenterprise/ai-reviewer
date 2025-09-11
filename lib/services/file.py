import asyncio
import mimetypes
import os
import argparse
from markitdown import MarkItDown

from lib.agents.markdown_cleaner import markdown_cleaner_agent


class File:
    def __init__(
        self, file_path: str, file_name: str | None = None, file_type: str | None = None
    ):
        if file_name is None:
            file_name = os.path.basename(file_path)
        if file_type is None:
            file_type = mimetypes.guess_type(file_path)[0]
        self.file_name = file_name
        self.file_path = file_path
        self.file_type = file_type  # mime type

        self._markdown = None

    async def get_markdown(self):
        if self._markdown is not None:
            return self._markdown
        md = MarkItDown(enable_plugins=False)  # Set to True to enable plugins
        result = md.convert(self.file_path)
        self._markdown = result.markdown
        # TODO: For PDFs, we may need something like this:
        # result = await markdown_cleaner_agent.apply(
        #     prompt_kwargs={
        #         "full_document": result.markdown,
        #     }
        # )
        # self._markdown = result.text
        return self._markdown
