from pydantic import BaseModel, Field
from lib.models import Agent

from langchain_core.prompts import ChatPromptTemplate

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class MarkdownCleanerResponse(BaseModel):
    text: str = Field(description="The cleaned markdown document")


markdown_cleaner_agent = Agent(
    name="Markdown Cleaner",
    description="Clean a markdown text",
    model="openai:gpt-4.1",
    prompt=SystemMessage(
        content="""You will be given a markdown document extracted from another document. There may be artifacts, for example extra new lines in the middle of sentences (because the original document may be a PDF). Remove any artifacts and return a clean markdown document with the exact same context. So in your response, there should not be any extra new line characters in the middle of sentences.

I will send the markdown document to clean as my next message."""
    )
    + "{full_document}",
    tools=[],
    mandatory_tools=[],
    output_schema=MarkdownCleanerResponse,
)
