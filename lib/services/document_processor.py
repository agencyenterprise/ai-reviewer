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

    async def apply_agent_to_all_chunks(
        self,
        agent: Agent,
        prompt_kwargs: dict | None = None,
        target_chunk_indices: list[int] | None = None,
        existing_results: list | None = None,
        default_response_factory=None,
        concurrency_limit: int = 3
    ):
        """
        Apply an agent to all chunks with support for selective processing and chunk reevaluation.
        
        Args:
            agent: The agent to apply
            prompt_kwargs: Additional prompt arguments
            target_chunk_indices: If provided, only process these chunk indices (for reevaluation)
            existing_results: Existing results to preserve when doing selective processing
            default_response_factory: Factory function to create empty/default responses
            concurrency_limit: Maximum number of concurrent chunk processing tasks
            
        Returns:
            List of results for all chunks
        """
        chunks = await self.get_chunks()
        
        if target_chunk_indices is not None:
            if existing_results is None:
                existing_results = []

            while len(existing_results) < len(chunks):
                if default_response_factory:
                    existing_results.append(default_response_factory())
                else:
                    existing_results.append(None)
            chunks_to_process = [(i, chunks[i]) for i in target_chunk_indices if i < len(chunks)]
            logger.info(f"Selective chunk processing: {target_chunk_indices}")
        else:
            if default_response_factory:
                existing_results = [default_response_factory() for _ in range(len(chunks))]
            else:
                existing_results = [None] * len(chunks)
            chunks_to_process = list(enumerate(chunks))
            logger.info(f"Full processing of {len(chunks)} chunks")

        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def process_chunk(chunk_idx, chunk):
            async with semaphore:
                try:
                    result_data = await self.apply_agent_to_chunk(
                        agent=agent,
                        chunk=chunk,
                        prompt_kwargs=prompt_kwargs
                    )
                    return result_data
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_idx} with agent {agent.name}: {e}")
                    if default_response_factory:
                        return default_response_factory()
                    else:
                        raise

        tasks = [process_chunk(chunk_idx, chunk) for chunk_idx, chunk in chunks_to_process]
        chunk_results = await run_tasks(tasks, desc=f"Processing chunks with {agent.name}")
        
        final_results = existing_results.copy()
        
        for (chunk_idx, _), result in zip(chunks_to_process, chunk_results):
            if isinstance(result, Exception):
                logger.error(f"Exception in chunk {chunk_idx}: {result}")
                if default_response_factory:
                    final_results[chunk_idx] = default_response_factory()
                else:
                    raise result
            else:
                final_results[chunk_idx] = result
        
        return final_results

    async def apply_agents_to_all_chunks(
        self,
        agents: list[Agent],
        prompt_kwargs: dict | None = None,
        target_chunk_indices: list[int] | None = None
    ):
        """Apply multiple agents to all chunks in parallel."""
        tasks = []
        for agent in agents:
            tasks.append(
                self.apply_agent_to_all_chunks(
                    agent, prompt_kwargs, target_chunk_indices
                )
            )
        return await run_tasks(
            tasks,
            desc=f"Processing chunks with {' & '.join([agent.name for agent in agents])}"
        )



if __name__ == "__main__":
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
        
        chunks = await processor.get_chunks()
        print(f"Document split into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"\nChunk {i}: {chunk.page_content[:100]}...")

    asyncio.run(main())
