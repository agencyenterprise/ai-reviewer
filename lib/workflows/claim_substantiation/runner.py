# Convenience helpers
import asyncio
import argparse
import logging
from typing import List, Optional

from lib.services.file import FileDocument, create_file_document_from_path
from lib.workflows.claim_substantiation.graph import build_claim_substantiator_graph
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState, DocumentChunk

logger = logging.getLogger(__name__)


async def run_claim_substantiator(
    file: FileDocument,
    supporting_files: Optional[List[FileDocument]] = None,
    use_toulmin: bool = False,
    target_chunk_indices: Optional[List[int]] = None,
    agents_to_run: Optional[List[str]] = None,
    existing_state: Optional[ClaimSubstantiatorState] = None,
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

    if existing_state is not None:
        state: ClaimSubstantiatorState = existing_state.copy()
        state["file"] = file
        if supporting_files is not None:
            state["supporting_files"] = supporting_files
    else:
        state: ClaimSubstantiatorState = {"file": file}
        if supporting_files is not None:
            state["supporting_files"] = supporting_files
    
    if target_chunk_indices is not None:
        state["target_chunk_indices"] = target_chunk_indices
    if agents_to_run is not None:
        state["agents_to_run"] = agents_to_run
        
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


def _reconstruct_file_document(file_dict: dict) -> FileDocument:
    """Helper to convert dictionary back to FileDocument object."""
    if isinstance(file_dict, dict):
        return FileDocument(
            fileName=file_dict.get("fileName", "unknown.md"),
            filePath=file_dict.get("filePath", "/tmp/temp"),
            fileType=file_dict.get("fileType", "text/markdown"),
            markdown=file_dict.get("markdown", "")
        )
    return file_dict


def _reconstruct_supporting_files(supporting_files_data: List) -> List[FileDocument]:
    """Helper to convert supporting files back to FileDocument objects."""
    supporting_files = []
    for sf in supporting_files_data:
        if isinstance(sf, dict):
            supporting_files.append(FileDocument(
                fileName=sf.get("fileName", "unknown.md"),
                filePath=sf.get("filePath", "/tmp/temp"),
                fileType=sf.get("fileType", "text/markdown"),
                markdown=sf.get("markdown", "")
            ))
        else:
            supporting_files.append(sf)
    return supporting_files


def _reconstruct_bibliography_item(ref_data):
    """Helper to safely reconstruct BibliographyItem with defaults for missing fields."""
    from lib.agents.reference_extractor import BibliographyItem
    
    if isinstance(ref_data, BibliographyItem):
        return ref_data
    
    ref_dict = ref_data if isinstance(ref_data, dict) else {}
    return BibliographyItem(
        text=ref_dict.get("text", ""),
        has_associated_supporting_document=ref_dict.get("has_associated_supporting_document", False),
        index_of_associated_supporting_document=ref_dict.get("index_of_associated_supporting_document", -1),
        name_of_associated_supporting_document=ref_dict.get("name_of_associated_supporting_document", "")
    )


def _reconstruct_state_from_result_dict(original_result: dict) -> ClaimSubstantiatorState:
    """Helper to convert API result dictionary back to ClaimSubstantiatorState."""
    from lib.agents.claim_detector import ClaimResponse
    from lib.agents.toulmin_claim_detector import ToulminClaimResponse  
    from lib.agents.citation_detector import CitationResponse
    from lib.agents.reference_extractor import BibliographyItem
    
    state: ClaimSubstantiatorState = {
        "file": _reconstruct_file_document(original_result.get("file", {})),
        "supporting_files": _reconstruct_supporting_files(original_result.get("supportingFiles", [])),
        "chunks": original_result.get("chunks", []),
        "references": [_reconstruct_bibliography_item(ref) 
                      for ref in original_result.get("references", [])],
        "claims_by_chunk": original_result.get("claimsByChunk", []),
        "citations_by_chunk": original_result.get("citationsByChunk", []),
        "claim_substantiations_by_chunk": original_result.get("claimSubstantiationsByChunk", [])
    }
    return state


async def reevaluate_single_chunk(
    original_result: dict,
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
    
    chunks = original_result.get("chunks", [])
    if chunk_index >= len(chunks):
        raise ValueError(f"Chunk index {chunk_index} out of range (max: {len(chunks)-1})")

    existing_state = _reconstruct_state_from_result_dict(original_result)

    updated_state = await run_claim_substantiator(
        file=existing_state["file"],
        supporting_files=existing_state.get("supporting_files"),
        use_toulmin=use_toulmin,
        target_chunk_indices=[chunk_index],
        agents_to_run=agents_to_run,
        existing_state=existing_state
    )

    chunk_content = chunks[chunk_index]

    claims = (updated_state.get("claims_by_chunk", [])[chunk_index] 
             if chunk_index < len(updated_state.get("claims_by_chunk", [])) else None)
    citations = (updated_state.get("citations_by_chunk", [])[chunk_index]
                if chunk_index < len(updated_state.get("citations_by_chunk", [])) else None)
    substantiation_chunk = (updated_state.get("claim_substantiations_by_chunk", [])[chunk_index]
                           if chunk_index < len(updated_state.get("claim_substantiations_by_chunk", [])) else None)
    substantiations = substantiation_chunk.substantiations if substantiation_chunk else []
    
    return DocumentChunk(
        content=chunk_content,
        chunk_index=chunk_index,
        claims=claims,
        citations=citations,
        substantiations=substantiations
    )


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