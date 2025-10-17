import logging
import os
from dataclasses import dataclass
from typing import List, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import create_async_engine

from lib.config.env import config

logger = logging.getLogger(__name__)

RAG_TOP_K = 10
RAG_CHUNK_SIZE = 1000
RAG_CHUNK_OVERLAP = 200


@dataclass
class RetrievedPassage:
    """Represents a passage retrieved from vector store."""

    content: str
    source_file: str
    chunk_index: int
    similarity_score: float
    page_number: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "source": self.source_file,
            "chunk_index": self.chunk_index,
            "similarity_score": round(self.similarity_score, 3),
            "page": self.page_number,
        }


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

        async_engine = create_async_engine(async_url)
        self.vectorstore = PGVector(
            connection=async_engine,
            embeddings=self.embeddings,
            collection_name="document_passages",
            use_jsonb=True,
        )
        logger.info("VectorStore initialized with async engine")

    async def collection_exists(self, collection_id: str) -> bool:
        """Check if collection already indexed."""
        try:
            results = await self.vectorstore.asimilarity_search(
                query="test",
                k=1,
                filter={"collection_id": collection_id},
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

            await self.vectorstore.aadd_documents(docs)

            logger.info(f"Indexed {len(docs)} chunks for {file_name}")
            return len(docs)

        except Exception as e:
            logger.error(f"Failed to index document {file_name}: {e}")
            raise

    async def retrieve_relevant_passages(
        self, query: str, collection_id: str, top_k: int = RAG_TOP_K
    ) -> List[RetrievedPassage]:
        """
        Retrieve most relevant passages for query.
        Returns empty list on failure for graceful degradation.
        """
        try:
            results = await self.vectorstore.asimilarity_search_with_score(
                query, k=top_k, filter={"collection_id": collection_id}
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
            logger.error(f"Retrieval failed for query '{query[:50]}...': {e}")
            return []


_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create singleton vector store service."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService(config.DATABASE_URL)
    return _vector_store_service
