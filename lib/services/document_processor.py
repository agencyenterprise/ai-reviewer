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

from lib.services.file import File
from lib.models import Agent

from lib.run_utils import run_tasks

logger = logging.getLogger(__name__)

underlying_embeddings = OpenAIEmbeddings()
store = LocalFileStore("./cache/embeddings")

cached_embedder = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings, store, namespace=underlying_embeddings.model
)


class DocumentProcessor:
    def __init__(
        self,
        file: File,
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
            chunker = RecursiveCharacterTextSplitter(
                chunk_size=1,
                chunk_overlap=0,
                separators=["\n\n", "\n"],
                keep_separator=False,
            )

        self.chunker = chunker

        self.file = file

        self._chunks = None

    async def _split_to_chunks(self):
        markdown = await self.file.get_markdown()
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
            filtered_kwargs["full_document"] = await self.file.get_markdown()
        if prompt_kwargs:
            for key, value in prompt_kwargs.items():
                if key in input_variables:
                    filtered_kwargs[key] = value
        return await agent.apply(filtered_kwargs)

    async def apply_agent_to_all_chunks(
        self, agent: Agent, prompt_kwargs: dict | None = None
    ):
        await self.file.get_markdown()  # Warm cache before running agents in parallel
        tasks = []
        chunks = await self.get_chunks()
        for chunk in chunks:
            tasks.append(self.apply_agent_to_chunk(agent, chunk, prompt_kwargs))

        chunk_results = await run_tasks(
            tasks, desc=f"Processing chunks with {agent.name}"
        )
        return chunk_results

    async def apply_agents_to_all_chunks(
        self, agents: list[list[Agent]], prompt_kwargs: dict | None = None
    ):
        await self.file.get_markdown()  # Warm cache before running agents in parallel
        tasks = []
        for agent in agents:
            tasks.append(self.apply_agent_to_all_chunks(agent, prompt_kwargs))
        return await run_tasks(
            tasks,
            desc=f"Processing chunks with {' & '.join([agent.name for agent in agents])}",
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
    file = File(file_path=args.file_path)
    processor = DocumentProcessor(file)

    from lib.agents.claim_detector import claim_detector_agent
    from lib.agents.citation_detector import citation_detector_agent
    from lib.agents.reference_extractor import reference_extractor_agent
    from lib.agents.reference_matcher import reference_matcher_agent

    results = asyncio.run(
        processor.apply_agents_to_all_chunks(
            [
                claim_detector_agent,
                citation_detector_agent,
            ]
        )
    )

    print(results)
