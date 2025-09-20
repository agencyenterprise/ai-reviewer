# Convenience helpers
import asyncio
import argparse
import logging
from typing import List, Optional

from lib.services.file import FileDocument, create_file_document_from_path
from lib.workflows.claim_substantiation.graph import build_claim_substantiator_graph
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)

logger = logging.getLogger(__name__)


async def run_claim_substantiator(
    file: FileDocument,
    supporting_files: Optional[List[FileDocument]] = None,
    use_toulmin: bool = False,
    target_chunk_indices: Optional[List[int]] = None,
    agents_to_run: Optional[List[str]] = None,
) -> ClaimSubstantiatorState:
    """
    Claim substantiation runner using LangGraph approach.

    Supports both full document processing and selective chunk re-evaluation:
    - For full processing: leave target_chunk_indices and agents_to_run as None
    - For selective re-evaluation: provide target_chunk_indices and/or agents_to_run
    - For re-evaluation with existing results: provide existing_state to preserve previous results

    This is the single, authoritative entry point for claim substantiation.
    """
    app = build_claim_substantiator_graph(use_toulmin=use_toulmin)

    state = ClaimSubstantiatorState(
        file=file,
        supporting_files=supporting_files,
        target_chunk_indices=target_chunk_indices,
        agents_to_run=agents_to_run,
    )

    return await app.ainvoke(state)


async def run_claim_substantiator_from_paths(
    file_path: str,
    supporting_paths: Optional[List[str]] = None,
    use_toulmin: bool = False,
):
    """Convenience function to run claim substantiator from file paths."""
    file = await create_file_document_from_path(file_path)
    supporting_files = (
        [await create_file_document_from_path(p) for p in supporting_paths]
        if supporting_paths
        else None
    )

    return await run_claim_substantiator(file, supporting_files, use_toulmin)


async def reevaluate_single_chunk(
    original_result: ClaimSubstantiatorState,
    chunk_index: int,
    agents_to_run: List[str],
    use_toulmin: bool = False,
) -> DocumentChunk:
    """
    Re-evaluate a single chunk using unified LangGraph approach.

    This function now leverages the enhanced LangGraph workflow with selective processing
    instead of manually calling agent registry functions.
    """
    logger.info(f"Re-evaluating chunk {chunk_index} with agents {agents_to_run}")

    chunks = original_result.chunks
    if chunk_index >= len(chunks):
        raise ValueError(
            f"Chunk index {chunk_index} out of range (max: {len(chunks)-1})"
        )

    app = build_claim_substantiator_graph(use_toulmin=use_toulmin)

    state = original_result.model_copy(
        update={
            "target_chunk_indices": [chunk_index],
            "agents_to_run": agents_to_run,
        }
    )

    result = await app.ainvoke(state)
    return result["chunks"][chunk_index]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "main_document_path", help="Path to the main document to analyze"
    )
    parser.add_argument(
        "supporting_documents",
        nargs="*",
        help="Paths to supporting documents (optional)",
    )
    parser.add_argument(
        "-t",
        "--use-toulmin",
        action="store_true",
        default=True,
        help="Use Toulmin claim detector",
    )
    args = parser.parse_args()

    result_state = asyncio.run(
        run_claim_substantiator_from_paths(
            args.main_document_path, args.supporting_documents, args.use_toulmin
        )
    )
    print("Result state:")
    print(result_state)
