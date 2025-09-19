import logging
from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)


async def prepare_documents(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    # Touch markdown for main and supporting docs to ensure they are loaded/cached

    logger.info("prepare_documents: preparing documents")

    processor = DocumentProcessor(state["file"])

    chunks = await processor.get_chunks()
    chunks_content = [chunk.page_content for chunk in chunks]

    return {
        "chunks": [
            DocumentChunk(content=chunk_content, chunk_index=index)
            for index, chunk_content in enumerate(chunks_content)
        ]
    }
