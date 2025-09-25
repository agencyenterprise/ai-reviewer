from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field

from lib.config.llm import models
from lib.models import Agent


class MarkdownCleanerResponse(BaseModel):
    text: str = Field(description="The cleaned markdown document")


markdown_cleaner_agent = Agent(
    name="Markdown Cleaner",
    description="Clean a markdown text",
    model=models["gpt-4.1"],
    prompt=SystemMessage(
        content="""You will be given a markdown document extracted from another document. There may be artifacts, for example extra new lines in the middle of sentences (because the original document may be a PDF). Remove any artifacts and return a clean markdown document with the exact same context. So in your response, there should not be any extra new line characters in the middle of sentences.

I will send the markdown document to clean as my next message."""
    )
    + "{full_document}",
    tools=[],
    mandatory_tools=[],
    output_schema=MarkdownCleanerResponse,
)
