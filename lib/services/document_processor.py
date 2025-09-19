import asyncio
import logging
import argparse

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from lib.services.file import FileDocument
from lib.models import Agent

from lib.run_utils import run_tasks
from lib.services.llm_test_splitter import LLMTextSplitter

logger = logging.getLogger(__name__)

underlying_embeddings = OpenAIEmbeddings()
store = LocalFileStore("./cache/embeddings")

cached_embedder = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings, store, namespace=underlying_embeddings.model
)


class DocumentProcessor:
    def __init__(
        self,
        file: FileDocument,
        chunker: SemanticChunker | None = None,
        embeddings: OpenAIEmbeddings | None = None,
    ):
        if embeddings is None:
            embeddings = cached_embedder
        self.embeddings = embeddings

        if chunker is None:
            # https://python.langchain.com/docs/how_to/semantic-chunker/
            # chunker = SemanticChunker(
            #     self.embeddings,
            #     breakpoint_threshold_type="percentile",
            #     # breakpoint_threshold_amount=0,
            # )
            # chunker = MarkdownTextSplitter()
            # chunker = RecursiveCharacterTextSplitter(
            #     chunk_size=1,
            #     chunk_overlap=0,
            #     separators=["\n\n", "\n"],
            #     keep_separator=False,
            # )
            chunker = LLMTextSplitter()

        self.chunker = chunker

        self.file = file

        self._chunks = None

    async def _split_to_chunks(self):
        markdown = self.file.markdown
        docs = self.chunker.create_documents([markdown])
        return docs

    async def get_chunks(self):
        if self._chunks is None:
            self._chunks = await self._split_to_chunks()
        return self._chunks

    async def apply_agent_to_chunk(
        self, agent: Agent, chunk: Document, prompt_kwargs: dict | None = None
    ):
        input_variables = set(
            getattr(agent.prompt, "input_variables", ["chunk", "full_document"])
        )
        filtered_kwargs: dict = {}
        if "chunk" in input_variables:
            filtered_kwargs["chunk"] = chunk.page_content
        if "full_document" in input_variables:
            filtered_kwargs["full_document"] = self.file.markdown
        if prompt_kwargs:
            for key, value in prompt_kwargs.items():
                if key in input_variables:
                    filtered_kwargs[key] = value
        return await agent.apply(filtered_kwargs)



if __name__ == "__main__":
    # For testing basic DocumentProcessor functionality
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file_path",
        nargs="?",
        type=str,
        default="/Users/omid/codes/rand-ai-reviewer/data/example_public_files/RAND_CFA4214-1-main.docx",
    )
    args = parser.parse_args()
    from lib.services.file import create_file_document_from_path
    import asyncio
    
    async def main():
        file = await create_file_document_from_path(args.file_path)
        processor = DocumentProcessor(file)
        
        # Test basic chunking functionality
        chunks = await processor.get_chunks()
        print(f"Document split into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"\nChunk {i}: {chunk.page_content[:100]}...")

    asyncio.run(main())
