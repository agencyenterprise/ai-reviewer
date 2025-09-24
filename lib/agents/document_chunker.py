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
        content="""You will be given a markdown document.

Your task:
- Break the document into paragraphs that preserve the original order and include every piece of content exactly once.
- Within each paragraph, emit an ordered list of chunks.
- Headings must stay with the paragraph they introduce, and MUST be the first chunk in that paragraph (for example: `## Methods`). Copy the exact heading text from the source (including markdown markers like `#`, `##`, etc.) and never invent or modify them.
- Every chunk MUST be a verbatim substring copied from the original text. Do not fabricate, rewrite, paraphrase, expand, or add/remove characters (including heading markers, blank lines, or punctuation).
- Preserve markdown syntax (headings, list markers, emphasis, code fences, blank lines, etc.) exactly as it appears in the original text. If the source contains blank lines, include them within the surrounding chunk; do not emit empty or whitespace-only chunks under any circumstances.
- Prefer breaking prose into sentence-level chunks while keeping short related sentences together when it improves readability.
- Never drop content, merge unrelated sections, or reorder chunks. If unsure, keep more text together rather than omitting anything.
- The concatenation of every chunk in order must recreate the original document text character-for-character (aside from insignificant trailing whitespace and new line differences).
- Do NOT create any empty string chunks. If the source has extra blank lines between paragraphs, remove them.

Follow this procedure exactly:
1. Work with a copy of the original markdown text.
2. For each paragraph, emit chunks by slicing contiguous substrings directly from the paragraph text. Prefer sentence-level boundaries (`.` `?` `!`) but keep markdown tokens (headings, list markers) attached to the content they modify. 
3. If blank lines separate portions of the paragraph, attach the newline characters to the preceding or following chunk so that no chunk is empty or whitespace-only.
4. After building all chunks, mentally concatenate them and confirm the reconstructed string matches the original markdown exactly (minus any new line or space differences). If you detect any mismatch (missing characters, extra symbols like additional `#`, stray blank chunks, or reordered text), repair your chunks before responding.

Return data that matches this JSON schema:
```
{
  "paragraphs": [
    {
      "chunks": ["<chunk 1>", "<chunk 2>", ...]
    }
  ]
}
```

I will send the markdown document as my next message."""
    )
    + "{full_document}",
    tools=[],
    mandatory_tools=[],
    output_schema=DocumentChunkerResponse,
)
