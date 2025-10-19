"""Reference providers for claim verification.

This module implements the Strategy pattern to provide references for claim verification
through different methods (citation-based vs RAG-based).
"""

import logging
from typing import List, Optional, Protocol, Tuple

from lib.agents.citation_detector import CitationResponse
from lib.agents.claim_extractor import Claim
from lib.agents.claim_verifier import RetrievedPassageInfo
from lib.agents.formatting_utils import (
    format_cited_references,
    format_retrieved_passages,
)
from lib.services.vector_store import (
    RetrievedPassage,
    get_collection_id,
    get_file_hash_from_path,
    get_vector_store_service,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)


class ReferenceProvider(Protocol):
    """Strategy for providing reference content to claim verifier."""

    async def get_references_for_claim(
        self,
        state: ClaimSubstantiatorState,
        chunk: DocumentChunk,
        claim: Claim,
        claim_index: int,
    ) -> Tuple[str, str, Optional[List[RetrievedPassageInfo]]]:
        """Get references for a claim.

        Returns:
            Tuple of (cited_references, cited_references_paragraph, retrieved_passages)
        """
        ...


class CitationBasedReferenceProvider:
    """Provides references from detected citations in the document."""

    async def get_references_for_claim(
        self,
        state: ClaimSubstantiatorState,
        chunk: DocumentChunk,
        claim: Claim,
        claim_index: int,
    ) -> Tuple[str, str, None]:
        """Get references based on detected citations."""

        cited_references = format_cited_references(
            state.references,
            state.supporting_files,
            chunk.citations,
            truncate_at_character_count=100000,
        )

        paragraph_chunks = state.get_paragraph_chunks(chunk.paragraph_index)
        paragraph_chunks_citations_not_in_chunk = [
            citation
            for other_chunk in paragraph_chunks
            if other_chunk != chunk
            and other_chunk.citations is not None
            and other_chunk.citations.citations
            for citation in other_chunk.citations.citations
            if chunk.citations is not None and citation not in chunk.citations.citations
        ]

        paragraph_other_chunk_citations = CitationResponse(
            citations=paragraph_chunks_citations_not_in_chunk,
            rationale="Citations in the paragraph that are not in the chunk",
        )

        cited_references_paragraph = format_cited_references(
            state.references,
            state.supporting_files,
            paragraph_other_chunk_citations,
            truncate_at_character_count=100000,
        )

        return cited_references, cited_references_paragraph, None


class RAGReferenceProvider:
    """Provides references via RAG retrieval from vector store."""

    async def get_references_for_claim(
        self,
        state: ClaimSubstantiatorState,
        chunk: DocumentChunk,
        claim: Claim,
        claim_index: int,
    ) -> Tuple[str, str, List[RetrievedPassageInfo]]:
        """Get references via RAG retrieval."""
        vector_store = get_vector_store_service()
        all_passages = []

        for file_doc in state.supporting_files or []:
            file_hash = get_file_hash_from_path(file_doc.file_path)
            collection_id = get_collection_id(file_hash)

            passages = await vector_store.retrieve_relevant_passages(
                query=claim.claim, collection_id=collection_id
            )
            all_passages.extend(passages)

        all_passages.sort(key=lambda p: p.similarity_score, reverse=True)
        top_passages = all_passages[:10]

        cited_references = format_retrieved_passages(top_passages)

        retrieved_passage_info = [
            RetrievedPassageInfo(
                content=p.content,
                source_file=p.source_file,
                similarity_score=p.similarity_score,
                chunk_index=p.chunk_index,
            )
            for p in top_passages
        ]

        return cited_references, "", retrieved_passage_info
