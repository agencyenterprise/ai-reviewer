import logging

from langchain_text_splitters.base import TextSplitter

from lib.agents.document_chunker import DocumentChunkerResponse, document_chunker_agent

logger = logging.getLogger(__name__)


class LLMTextSplitter(TextSplitter):
    def split_text(self, text: str) -> list[str]:
        result: DocumentChunkerResponse = document_chunker_agent.apply_sync(
            prompt_kwargs={
                "full_document": text,
            }
        )
        return result.chunks
