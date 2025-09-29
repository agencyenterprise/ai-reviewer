# Convenience helpers
import argparse
import asyncio
import logging
from typing import List, Optional

from lib.services.file import FileDocument, create_file_document_from_path
from lib.workflows.claim_substantiation.graph import build_claim_substantiator_graph

from lib.workflows.citation_suggestion.state import (
    CitationSuggestionState,
    CitationSuggestionWorkflowConfig,
)

logger = logging.getLogger(__name__)


async def run_citation_suggestion(
    file: FileDocument,
    supporting_files: Optional[List[FileDocument]] = None,
    config: SubstantiationWorkflowConfig = None,
) -> CitationSuggestionState:
    """
    Claim substantiation runner using LangGraph approach.

    Supports both full document processing and selective chunk re-evaluation:
    - For full processing: leave config.target_chunk_indices and config.agents_to_run as None
    - For selective re-evaluation: provide config.target_chunk_indices and/or config.agents_to_run
    - For re-evaluation with existing results: provide existing_state to preserve previous results

    This is the single, authoritative entry point for claim substantiation.
    """

    if config is None:
        config = SubstantiationWorkflowConfig()

    app = build_claim_substantiator_graph(
        use_toulmin=config.use_toulmin, session_id=config.session_id
    )

    state = ClaimSubstantiatorState(
        file=file,
        supporting_files=supporting_files,
        config=config,
    )

    return await app.ainvoke(state)


async def run_claim_substantiator_from_paths(
    file_path: str,
    supporting_paths: Optional[List[str]] = None,
    config: SubstantiationWorkflowConfig = None,
):
    """Convenience function to run claim substantiator from file paths."""
    file = await create_file_document_from_path(file_path)
    supporting_files = (
        [await create_file_document_from_path(p) for p in supporting_paths]
        if supporting_paths
        else None
    )

    return await run_claim_substantiator(file, supporting_files, config)


async def reevaluate_single_chunk(
    original_result: ClaimSubstantiatorState,
    chunk_index: int,
    agents_to_run: List[str],
    config_overrides: SubstantiationWorkflowConfig = None,
) -> ClaimSubstantiatorState:
    """
    Re-evaluate a single chunk using unified LangGraph approach.
    """
    logger.info(f"Re-evaluating chunk {chunk_index} with agents {agents_to_run}")

    chunks = original_result.chunks
    if chunk_index >= len(chunks):
        raise ValueError(
            f"Chunk index {chunk_index} out of range (max: {len(chunks)-1})"
        )

    # Create updated config with overrides
    config = original_result.config.model_copy()
    if config_overrides:
        # Update config with any provided overrides
        config = config.model_copy(
            update=config_overrides.model_dump(exclude_none=True)
        )

    # Always override target_chunk_indices and agents_to_run for this specific operation
    config.target_chunk_indices = [chunk_index]
    config.agents_to_run = agents_to_run

    app = build_claim_substantiator_graph(
        use_toulmin=config.use_toulmin,
        session_id=config.session_id or original_result.session_id,
    )

    state = original_result.model_copy(
        update={
            "target_chunk_indices": [chunk_index],
            "agents_to_run": agents_to_run,
            "errors": [
                error
                for error in original_result.errors
                if error.chunk_index != chunk_index
            ],
            "config": config,
        }
    )

    updated_state = await app.ainvoke(state)
    return updated_state


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

    config = SubstantiationWorkflowConfig(use_toulmin=args.use_toulmin)
    result_state = asyncio.run(
        run_claim_substantiator_from_paths(
            args.main_document_path, args.supporting_documents, config
        )
    )
    print("Result state:")
    print(result_state)
