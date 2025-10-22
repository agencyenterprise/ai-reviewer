import asyncio
import logging

from langchain_core.documents import Document
from langchain_text_splitters.base import TextSplitter

from lib.agents.document_chunker import (
    document_chunker_agent,
    get_chunker_result_as_langchain_documents,
)

logger = logging.getLogger(__name__)


class LLMTextSplitter(TextSplitter):
    async def split_text(self, text: str) -> list[str]:
        result = await document_chunker_agent.ainvoke(
            prompt_kwargs={
                "full_document": text,
            }
        )
        return get_chunker_result_as_langchain_documents(result)

    async def create_documents(
        self, texts: list[str], metadatas: list[dict] = None
    ) -> list[Document]:
        split_tasks = [self.split_text(text) for text in texts]
        async_results = await asyncio.gather(*split_tasks, return_exceptions=True)
        docs = []
        for result in async_results:
            if isinstance(result, Exception):
                raise result
            docs.extend(result)
        return docs
