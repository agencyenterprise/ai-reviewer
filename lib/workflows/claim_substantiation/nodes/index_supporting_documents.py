import logging

from lib.services.vector_store import (
    get_collection_id,
    get_file_hash_from_path,
    get_vector_store_service,
)
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


async def index_supporting_documents(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    """
    Index supporting documents for RAG retrieval.
    Skips if use_rag is False or no supporting files provided.
    """
    if not state.config.use_rag:
        logger.info("RAG disabled, skipping indexing")
        return {}

    if not state.supporting_files:
        logger.info("No supporting files to index")
        return {}

    logger.info(f"Indexing {len(state.supporting_files)} supporting documents for RAG")

    vector_store = get_vector_store_service()
    indexed_collections = {}

    for file_doc in state.supporting_files:
        try:
            file_hash = get_file_hash_from_path(file_doc.file_path)
            collection_id = get_collection_id(file_hash)

            if await vector_store.collection_exists(collection_id):
                logger.info(
                    f"Collection {collection_id} exists, skipping {file_doc.file_name}"
                )
                indexed_collections[file_hash] = collection_id
                continue

            num_chunks = await vector_store.index_document(
                markdown_content=file_doc.markdown,
                file_name=file_doc.file_name,
                collection_id=collection_id,
            )

            indexed_collections[file_hash] = collection_id
            logger.info(f"Indexed {num_chunks} chunks for {file_doc.file_name}")

        except Exception as e:
            logger.error(f"Failed to index {file_doc.file_name}: {e}")

    return {"indexed_collections": indexed_collections}
