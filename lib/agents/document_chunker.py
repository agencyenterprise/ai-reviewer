from pydantic import BaseModel, Field
from lib.models import Agent

from langchain_core.prompts import ChatPromptTemplate

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class DocumentChunkerResponse(BaseModel):
    chunks: list[str] = Field(
        description="The chunks extracted from the document, that when concatenated should recreate the content of the original document"
    )


document_chunker_agent = Agent(
    name="Document Chunker",
    description="Chunk a document into reasonable sentence-level chunks",
    model="google_genai:gemini-2.5-flash-lite",
    prompt=SystemMessage(
        content="""You will be given a markdown document. Your task is to break the document into reasonable sentence-level chunks. The chunks you return should be in order, and whe concatenated, should recreate the content of the original document (except differences in new lines and whitespace and formatting).

I will send the markdown document as my next message."""
    )
    + "{full_document}",
    mandatory_tools=[],
    output_schema=DocumentChunkerResponse,
)
