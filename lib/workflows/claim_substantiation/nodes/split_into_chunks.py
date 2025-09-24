import logging

from langchain.embeddings import CacheBackedEmbeddings, OpenAIEmbeddings
from langchain.storage import LocalFileStore
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)

from lib.services.llm_test_splitter import LLMTextSplitter
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)


logger = logging.getLogger(__name__)


underlying_embeddings = OpenAIEmbeddings()
store = LocalFileStore("./cache/embeddings")
cached_embedder = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings, store, namespace=underlying_embeddings.model
)

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


async def split_into_chunks(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    logger.info("split_into_chunks: splitting into chunks")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "citations" not in agents_to_run:
        logger.info(
            "split_into_chunks: Skipping split_into_chunks (not in agents_to_run)"
        )
        return {}

    markdown = state.file.markdown
    docs = chunker.create_documents([markdown])

    return {
        "chunks": [
            DocumentChunk(content=doc.page_content, chunk_index=index)
            for index, doc in enumerate(docs)
        ]
    }
