import logging

from langchain.embeddings import CacheBackedEmbeddings, OpenAIEmbeddings
from langchain.storage import LocalFileStore

from lib.run_utils import call_maybe_async
from lib.services.llm_text_splitter import LLMTextSplitter
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)


logger = logging.getLogger(__name__)


# underlying_embeddings = OpenAIEmbeddings()
# store = LocalFileStore("./cache/embeddings")
# cached_embedder = CacheBackedEmbeddings.from_bytes_store(
#     underlying_embeddings, store, namespace=underlying_embeddings.model
# )

# chunker = SemanticChunker(
#     cached_embedder,
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


async def prepare_documents(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("prepare_documents: preparing documents")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "prepare_documents" not in agents_to_run:
        logger.info(
            "prepare_documents: Skipping prepare_documents (not in agents_to_run)"
        )
        return {}

    markdown = state.file.markdown  # To extract markdown from the main document

    return {}
