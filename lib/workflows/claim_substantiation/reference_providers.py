"""Reference providers for claim verification.

This module implements the Strategy pattern to provide references for claim verification
through different methods (citation-based vs RAG-based).
"""

import asyncio
import logging
from typing import List, Optional, Protocol

from pydantic import BaseModel, Field

from lib.agents.citation_detector import CitationResponse
from lib.agents.claim_extractor import Claim
from lib.agents.claim_verifier import RetrievedPassageInfo
from lib.agents.formatting_utils import (
    format_cited_references,
    format_retrieved_passages,
)
from lib.services.vector_store import (
    RAG_TOP_K,
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

# Citation-based reference provider settings
MAX_REFERENCE_CHARACTER_COUNT = 100000  # Max characters from full documents

# RAG reference provider settings
MAX_DISTANCE_THRESHOLD = (
    0.35  # Max cosine distance for passage relevance (0-1 scale, lower = more similar)
)
MAX_QUERY_LENGTH = 3000  # Max characters in enriched query
MAX_BACKING_ITEM_LENGTH = 600  # Max characters per backing item to include in query


class ReferenceContext(BaseModel):
    """Context containing references for claim verification."""

    cited_references: str = Field(
        description="Formatted references cited in the current chunk"
    )
    cited_references_paragraph: str = Field(
        description="Formatted references from other chunks in the same paragraph"
    )
    retrieved_passages: Optional[List[RetrievedPassageInfo]] = Field(
        default=None, description="Passages retrieved via RAG for this claim"
    )


class ReferenceProvider(Protocol):
    """Strategy for providing reference content to claim verifier."""

    async def get_references_for_claim(
        self,
        state: ClaimSubstantiatorState,
        chunk: DocumentChunk,
        claim: Claim,
        claim_index: int,
    ) -> ReferenceContext:
        """Get references for a claim."""
        ...


class CitationBasedReferenceProvider:
    """Provides references from detected citations in the document."""

    async def get_references_for_claim(
        self,
        state: ClaimSubstantiatorState,
        chunk: DocumentChunk,
        claim: Claim,
        claim_index: int,
    ) -> ReferenceContext:
        """Get references based on detected citations."""
        cited_references = format_cited_references(
            state.references,
            state.supporting_files,
            chunk.citations,
            truncate_at_character_count=MAX_REFERENCE_CHARACTER_COUNT,
        )

        paragraph_chunks_citations_not_in_chunk = (
            self._get_paragraph_citations_not_in_chunk(state, chunk)
        )

        paragraph_other_chunk_citations = CitationResponse(
            citations=paragraph_chunks_citations_not_in_chunk,
            rationale="Citations in the paragraph that are not in the chunk",
        )

        cited_references_paragraph = format_cited_references(
            state.references,
            state.supporting_files,
            paragraph_other_chunk_citations,
            truncate_at_character_count=MAX_REFERENCE_CHARACTER_COUNT,
        )

        return ReferenceContext(
            cited_references=cited_references,
            cited_references_paragraph=cited_references_paragraph,
        )

    def _get_paragraph_citations_not_in_chunk(
        self, state: ClaimSubstantiatorState, chunk: DocumentChunk
    ) -> List:
        """Extract citations from paragraph chunks that aren't in current chunk."""
        paragraph_chunks = state.get_paragraph_chunks(chunk.paragraph_index)
        citations_not_in_chunk = []

        for other_chunk in paragraph_chunks:
            if other_chunk == chunk:
                continue
            if not other_chunk.citations or not other_chunk.citations.citations:
                continue

            if not chunk.citations:
                citations_not_in_chunk.extend(other_chunk.citations.citations)
            else:
                for citation in other_chunk.citations.citations:
                    if citation not in chunk.citations.citations:
                        citations_not_in_chunk.append(citation)

        return citations_not_in_chunk


class RAGReferenceProvider:
    """Provides references via RAG retrieval from vector store."""

    async def get_references_for_claim(
        self,
        state: ClaimSubstantiatorState,
        chunk: DocumentChunk,
        claim: Claim,
        claim_index: int,
    ) -> ReferenceContext:
        """
        Get references via RAG retrieval.

        Retrieves relevant passages from ALL supporting documents and lets the
        claim verifier LLM determine if they support/don't support the claim.
        """
        if not state.supporting_files:
            logger.warning(
                f"No supporting files for RAG retrieval on claim {claim_index}"
            )
            return ReferenceContext(cited_references="", cited_references_paragraph="")

        try:
            vector_store = get_vector_store_service()

            query = self._build_enriched_query(chunk, claim)

            logger.debug(f"RAG query for claim {claim_index}: '{query}.'")

            retrieval_tasks = [
                vector_store.retrieve_relevant_passages(
                    query=query,
                    collection_id=get_collection_id(
                        get_file_hash_from_path(file_doc.file_path)
                    ),
                )
                for file_doc in state.supporting_files
            ]

            results = await asyncio.gather(*retrieval_tasks)
            all_passages = [passage for passages in results for passage in passages]

            all_passages.sort(key=lambda p: p.similarity_score, reverse=False)

            quality_passages = [
                p for p in all_passages if p.similarity_score <= MAX_DISTANCE_THRESHOLD
            ]
            top_passages = quality_passages[:RAG_TOP_K]

            logger.info(
                f"Retrieved {len(top_passages)} passages for claim {claim_index} "
                f"from {len(state.supporting_files)} files "
                f"({len(all_passages)} total passages, {len(quality_passages)} below threshold)"
            )

            if top_passages:
                logger.debug(
                    f"Top passage: {top_passages[0].source_file} "
                    f"(distance: {top_passages[0].similarity_score:.3f})"
                )

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

            return ReferenceContext(
                cited_references=cited_references,
                cited_references_paragraph="",
                retrieved_passages=retrieved_passage_info,
            )

        except Exception as e:
            logger.error(
                f"RAG retrieval failed for claim {claim_index}: {e}",
                exc_info=True,
            )
            return ReferenceContext(cited_references="", cited_references_paragraph="")

    def _build_enriched_query(self, chunk: DocumentChunk, claim: Claim) -> str:
        """
        Build an enriched query by combining the claim with citation and backing context.
        This helps the embedding model match the right document by adding author names
        and key contextual information.
        Handles both regular Claim and ToulminClaim.
        """
        query_parts = [claim.claim]

        if chunk.citations and chunk.citations.citations:
            citation_texts = [c.text for c in chunk.citations.citations]
            query_parts.extend(citation_texts)

        if hasattr(claim, "backing") and claim.backing:
            backing_texts = [
                b for b in claim.backing if len(b) < MAX_BACKING_ITEM_LENGTH
            ]
            query_parts.extend(backing_texts)

        enriched_query = " ".join(query_parts)

        if len(enriched_query) > MAX_QUERY_LENGTH:
            enriched_query = enriched_query[:MAX_QUERY_LENGTH]

        return enriched_query
