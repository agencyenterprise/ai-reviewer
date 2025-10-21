import logging
import os
from typing import List, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import create_async_engine

from lib.config.env import config

logger = logging.getLogger(__name__)

# RAG retrieval settings
RAG_TOP_K = 30  # Number of passages to retrieve per query

# RAG chunking settings (all in characters)
RAG_CHUNK_SIZE = 2000  # Characters per chunk when indexing documents
RAG_CHUNK_OVERLAP = 400  # Character overlap between adjacent chunks


class RetrievedPassage(BaseModel):
    """Represents a passage retrieved from vector store."""

    content: str = Field(description="The text content of the retrieved passage")
    source_file: str = Field(description="Name of the source file")
    chunk_index: int = Field(description="Index of the chunk within the source")
    similarity_score: float = Field(description="Cosine similarity score (0-1)")
    page_number: Optional[str] = Field(
        default=None, description="Page number if available"
    )


def get_file_hash_from_path(file_path: str) -> str:
    """Extract xxh128 hash from file path where hash is the filename."""
    return os.path.basename(file_path)


def get_collection_id(file_hash: str) -> str:
    """Generate pgvector collection ID from file hash."""
    return f"doc_passages_{file_hash[:16]}"


class VectorStoreService:
    """Service for vector storage and retrieval operations."""

    def __init__(self, connection_string: str):
        """Initialize vector store with database connection."""
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        self.chunker = RecursiveCharacterTextSplitter(
            chunk_size=RAG_CHUNK_SIZE,
            chunk_overlap=RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Always use async engine since all our methods are async
        # Convert postgresql:// to postgresql+psycopg:// for SQLAlchemy async engine
        if connection_string.startswith("postgresql://"):
            async_url = connection_string.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        else:
            async_url = connection_string

        self.async_engine = create_async_engine(async_url)
        self._vectorstore_cache: dict[str, PGVector] = {}

        logger.info("VectorStore initialized with async engine")

    def _get_vectorstore(self, collection_id: str) -> PGVector:
        """
        Get or create a PGVector instance for a specific collection.
        Each document gets its own collection for efficient retrieval.
        """
        if collection_id not in self._vectorstore_cache:
            self._vectorstore_cache[collection_id] = PGVector(
                connection=self.async_engine,
                embeddings=self.embeddings,
                collection_name=collection_id,  # Each document has its own collection
                use_jsonb=True,
            )
            logger.debug(f"Created PGVector instance for collection: {collection_id}")

        return self._vectorstore_cache[collection_id]

    async def collection_exists(self, collection_id: str) -> bool:
        """Check if collection already indexed."""
        try:
            vectorstore = self._get_vectorstore(collection_id)
            results = await vectorstore.asimilarity_search(
                query="test",
                k=1,
            )
            return len(results) > 0
        except Exception:
            return False

    async def index_document(
        self, markdown_content: str, file_name: str, collection_id: str
    ) -> int:
        """
        Chunk, embed, and index document.
        Returns number of chunks indexed.
        """
        try:
            if await self.collection_exists(collection_id):
                logger.info(
                    f"Collection {collection_id} already exists, skipping indexing"
                )
                return 0

            docs = self.chunker.create_documents(
                [markdown_content],
                metadatas=[
                    {"file_name": file_name, "collection_id": collection_id}
                    for _ in range(len(markdown_content))
                ],
            )

            for i, doc in enumerate(docs):
                doc.metadata["chunk_index"] = i
                doc.metadata["file_name"] = file_name
                doc.metadata["collection_id"] = collection_id

            vectorstore = self._get_vectorstore(collection_id)
            await vectorstore.aadd_documents(docs)

            logger.info(
                f"Indexed {len(docs)} chunks for {file_name} in collection {collection_id}"
            )
            return len(docs)

        except Exception as e:
            logger.error(f"Failed to index document {file_name}: {e}")
            raise

    async def retrieve_relevant_passages(
        self, query: str, collection_id: str, top_k: int = RAG_TOP_K
    ) -> List[RetrievedPassage]:
        """
        Retrieve most relevant passages for query from a SPECIFIC collection.
        Each document has its own collection, so no filtering needed.
        Returns empty list on failure for graceful degradation.
        """
        try:
            vectorstore = self._get_vectorstore(collection_id)

            results = await vectorstore.asimilarity_search_with_score(query, k=top_k)

            logger.info(
                f"Retrieved {len(results)} passages from collection {collection_id} "
                f"for query: '{query}.'"
            )

            passages = []
            for doc, score in results:
                passages.append(
                    RetrievedPassage(
                        content=doc.page_content,
                        source_file=doc.metadata.get("file_name", "unknown"),
                        chunk_index=doc.metadata.get("chunk_index", 0),
                        similarity_score=float(score),
                        page_number=doc.metadata.get("page_number"),
                    )
                )

            return passages

        except Exception as e:
            logger.error(f"Retrieval failed for query '{query}...': {e}")
            return []


_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create singleton vector store service."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService(config.DATABASE_URL)
    return _vector_store_service
