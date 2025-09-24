from langchain_core.messages import SystemMessage
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from lib.models import Agent
from lib.agents.models import ValidatedDocument


class Paragraph(BaseModel):
    chunks: list[str] = Field(
        description="The chunks extracted from the paragraph, that when concatenated should recreate the content of the original paragraph"
    )


class DocumentChunkerResponse(BaseModel):
    paragraphs: list[Paragraph] = Field(
        description="The paragraphs extracted from the document, each with sentence-level chunks. When these chunks are all concatenated, they should recreate the content of the original document"
    )

    def get_as_langchain_documents(self) -> list[ValidatedDocument]:
        chunks = []
        chunk_index = 0
        for paragraph_index, paragraph in enumerate(self.paragraphs):
            for index_within_paragraph, chunk in enumerate(paragraph.chunks):
                chunks.append(
                    ValidatedDocument(
                        page_content=chunk,
                        metadata={
                            "paragraph_index": paragraph_index,
                            "chunk_index": chunk_index,
                            "chunk_index_within_paragraph": index_within_paragraph,
                        },
                    )
                )
                chunk_index += 1
        return chunks


document_chunker_agent = Agent(
    name="Document Chunker",
    description="Chunk a document into paragraphs and each paragraph into reasonable sentence-level chunks",
    model="google_genai:gemini-2.5-flash-lite",
    prompt=SystemMessage(
        content="""You will be given a markdown document. Your task is to break the document into paragraphs and each paragraph into reasonable sentence-level chunks. The paragraphs and the chunks within them that you return should be in order, and when concatenated, should recreate the content of the original document (except differences in new lines and whitespace and formatting).

I will send the markdown document as my next message."""
    )
    + "{full_document}",
    tools=[],
    mandatory_tools=[],
    output_schema=DocumentChunkerResponse,
)
