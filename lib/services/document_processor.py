import argparse
import asyncio
import logging
from langchain.text_splitter import MarkdownTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain_core.documents import Document


from tqdm import tqdm

from lib.services.file import File
from lib.models import Agent

logger = logging.getLogger(__name__)

underlying_embeddings = OpenAIEmbeddings()
store = LocalFileStore("./cache/embeddings")

cached_embedder = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings, store, namespace=underlying_embeddings.model
)


async def run_tasks(tasks, desc="Processing tasks"):
    async def track_task(index, coro):
        try:
            return index, await coro
        except Exception as e:
            return index, e

    wrapped_tasks = [track_task(i, coro) for i, coro in enumerate(tasks)]

    chunk_results_dict = {}
    for finished_task in tqdm(
        asyncio.as_completed(wrapped_tasks),
        total=len(tasks),
        desc=desc,
    ):
        original_index, result_or_exception = await finished_task
        chunk_results_dict[original_index] = result_or_exception
        if isinstance(result_or_exception, Exception):
            logger.error(
                f"Error processing task {original_index}: {result_or_exception}",
                exc_info=True,
            )

    chunk_results = []
    for chunk_index in range(len(tasks)):
        if chunk_index not in chunk_results_dict:
            chunk_results.append(None)
        else:
            chunk_results.append(chunk_results_dict[chunk_index])
    return chunk_results


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
            chunker = SemanticChunker(
                self.embeddings,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=0,
            )
            # chunker = MarkdownTextSplitter(chunk_size=200, chunk_overlap=0)
            # chunker = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=0)

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

    async def apply_agent_to_chunk(self, agent: Agent, chunk: Document):
        return await agent.apply(
            prompt_kwargs={
                "chunk": chunk.page_content,
                "full_document": await self.file.get_markdown(),
            }
        )

    async def apply_agent_to_all_chunks(self, agent: Agent):
        markdown = (
            await self.file.get_markdown()
        )  # Just to make sure we have the markdown before running agents in parallel
        tasks = []
        chunks = await self.get_chunks()
        for chunk in chunks:
            tasks.append(self.apply_agent_to_chunk(agent, chunk))

        chunk_results = await run_tasks(
            tasks, desc=f"Processing chunks with {agent.name}"
        )
        return chunk_results

    async def apply_agents_to_all_chunks(self, agents: list[list[Agent]]):
        markdown = (
            await self.file.get_markdown()
        )  # Just to make sure we have the markdown before running agents in parallel
        tasks = []
        for agent in agents:
            tasks.append(self.apply_agent_to_all_chunks(agent))
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

    results = asyncio.run(
        processor.apply_agents_to_all_chunks(
            [
                claim_detector_agent,
                citation_detector_agent,
            ]
        )
    )

    print(results)
