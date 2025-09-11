from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, END
from pathlib import Path
from lib.services.file import File
from lib.services.document_processor import DocumentProcessor

from lib.agents.claim_detector import claim_detector_agent, ClaimResponse
from lib.agents.citation_detector import (
    citation_detector_agent,
    CitationResponse,
)
from lib.agents.reference_extractor import (
    reference_extractor_agent,
    ReferenceExtractorResponse,
)
from lib.agents.reference_matcher import (
    reference_matcher_agent,
    ReferenceMatch,
)
from lib.agents.claim_substantiator import (
    claim_substantiator_agent,
    ClaimSubstantiationResult,
)
from lib.agents.tools import format_supporting_documents_prompt_section
from lib.run_utils import run_tasks


class ClaimSubstantiatorState(TypedDict, total=False):
    file: File
    supporting_files: List[File]

    # Outputs
    claims_by_chunk: List[ClaimResponse]
    citations_by_chunk: List[CitationResponse]
    references: List[str]
    matches: List[ReferenceMatch]
    claim_substantiations_by_chunk: List[List[ReferenceMatch]]


async def prepare_documents(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    # Touch markdown for main and supporting docs to ensure they are loaded/cached
    await state["file"].get_markdown()
    for supporting_file in state.get("supporting_files", []) or []:
        await supporting_file.get_markdown()
    return {}


async def detect_claims(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    processor = DocumentProcessor(state["file"])
    results: List[ClaimResponse] = await processor.apply_agent_to_all_chunks(
        claim_detector_agent
    )
    return {"claims_by_chunk": results}


async def detect_citations(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    processor = DocumentProcessor(state["file"])
    bibliography = ""
    for index, reference in enumerate(state.get("references", [])):
        bibliography += f"""### Bibliography entry #{index + 1}
{reference}\n\n"""
    results: List[CitationResponse] = await processor.apply_agent_to_all_chunks(
        citation_detector_agent,
        prompt_kwargs={"bibliography": bibliography},
    )
    return {"citations_by_chunk": results}


async def extract_references(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    markdown = await state["file"].get_markdown()
    supporting_documents = "\n\n".join(
        [
            f"""### Supporting document #{index + 1}
{await format_supporting_documents_prompt_section(doc, truncate_at_character_count=1000)}
"""
            for index, doc in enumerate(state.get("supporting_files", []) or [])
        ]
    )
    res: ReferenceExtractorResponse = await reference_extractor_agent.apply(
        {"full_document": markdown, "supporting_documents": supporting_documents}
    )
    return {"references": res.references}


async def match_references(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    if not state.get("references") or not state.get("supporting_files"):
        return {}

    references = state["references"]
    matches: List[ReferenceMatch] = []

    for supporting_file in state["supporting_files"]:
        supporting_preview = await format_supporting_documents_prompt_section(
            supporting_file
        )
        try:
            match: Optional[ReferenceMatch] = await reference_matcher_agent.apply(
                {"references": references, "supporting_document": supporting_preview}
            )
            if match:
                matches.append(match)
        except Exception:
            # Best-effort matching per supporting file
            continue

    return {"matches": matches}


async def substantiate_claims(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    # Require claims and citations to be present
    if not state.get("claims_by_chunk") or not state.get("citations_by_chunk"):
        return {}

    processor = DocumentProcessor(state["file"])
    chunks = await processor.get_chunks()
    full_document = await state["file"].get_markdown()
    supporting_files = state.get("supporting_files", [])

    references = state.get("references", [])
    # Find all unsubstantiated claims
    tasks = []
    chunk_indices_with_tasks = []
    for chunk_index, (chunk, chunk_claims, citations) in enumerate(
        zip(chunks, state["claims_by_chunk"], state["citations_by_chunk"])
    ):
        unsubstantiated_claims = [
            c for c in chunk_claims.claims if c.needs_substantiation
        ]
        if unsubstantiated_claims:
            associated_bibliography_indices = [
                c.index_of_associated_bibliography
                for c in citations.citations
                if c.associated_bibliography
            ]
            claims_str = ""
            for index, claim in enumerate(unsubstantiated_claims):
                claims_str += f"### Claim #{index + 1}\n{claim.text}\n\n"
            cited_references_str = ""
            for bibliography_index in associated_bibliography_indices:
                cited_references_str += f"""### Cited bibliography entry #{bibliography_index}
Bibliography entry text: {references[bibliography_index-1].text}
"""
                if references[
                    bibliography_index - 1
                ].has_associated_supporting_document:
                    supporting_file = supporting_files[
                        references[
                            bibliography_index - 1
                        ].index_of_associated_supporting_document
                    ]
                    cited_references_str += (
                        await format_supporting_documents_prompt_section(
                            supporting_file
                        )
                    )
                else:
                    cited_references_str += "No associated supporting document provided by the user, so this bibliography item cannot be used to substantiate the claim\n\n"

                cited_references_str += "\n\n"

                tasks.append(
                    claim_substantiator_agent.apply(
                        {
                            "full_document": full_document,
                            "chunk": chunk.page_content,
                            "claim": claims_str,
                            "cited_references": cited_references_str,
                        }
                    )
                )
                chunk_indices_with_tasks.append(chunk_index)

    chunk_results = await run_tasks(
        tasks, desc="Processing chunks with Claim Substantiator"
    )
    claim_substantiations_by_chunk = [[] for _ in range(len(chunks))]
    for chunk_index, result in zip(chunk_indices_with_tasks, chunk_results):
        claim_substantiations_by_chunk[chunk_index].append(result)

    return {"claim_substantiations_by_chunk": claim_substantiations_by_chunk}


def build_claim_substantiator_graph():
    graph = StateGraph(ClaimSubstantiatorState)

    graph.add_node("prepare_documents", prepare_documents)
    graph.add_node("detect_claims", detect_claims)
    graph.add_node("detect_citations", detect_citations)
    graph.add_node("extract_references", extract_references)
    graph.add_node("substantiate_claims", substantiate_claims)

    graph.set_entry_point("prepare_documents")
    graph.add_edge("prepare_documents", "extract_references")
    graph.add_edge("prepare_documents", "detect_claims")
    graph.add_edge("extract_references", "detect_citations")

    # Trigger substantiation once claims and citations are likely present
    graph.add_edge("detect_citations", "substantiate_claims")
    graph.add_edge("detect_claims", "substantiate_claims")

    return graph.compile()


# Convenience helpers
async def run_claim_substantiator(
    file: File, supporting_files: Optional[List[File]] = None
):
    app = build_claim_substantiator_graph()
    state: ClaimSubstantiatorState = {"file": file}
    if supporting_files is not None:
        state["supporting_files"] = supporting_files
    return await app.ainvoke(state)


async def run_claim_substantiator_from_paths(
    file_path: str, supporting_paths: Optional[List[str]] = None
):
    file = File(file_path=file_path)
    supporting_files = (
        [File(file_path=p) for p in supporting_paths] if supporting_paths else None
    )
    await file.get_markdown()
    for supporting_file in supporting_files or []:
        await supporting_file.get_markdown()
    return await run_claim_substantiator(file, supporting_files)


if __name__ == "__main__":
    import argparse
    import asyncio

    data_dir = Path(__file__).parent.parent.parent / "tests" / "data"
    parser = argparse.ArgumentParser(description="Run Claim Substantiator workflow")
    parser.add_argument(
        "main_document_path",
        nargs="?",
        type=str,
        help="Path to the main document",
        default=data_dir / "main_document.md",
    )
    parser.add_argument(
        "-s",
        "--supporting-documents",
        nargs="?",
        action="append",
        default=[
            data_dir / "supporting_1.md",
            data_dir / "supporting_2.md",
            data_dir / "supporting_3.md",
        ],
        help="Path to a supporting document (repeatable)",
    )
    args = parser.parse_args()

    result_state = asyncio.run(
        run_claim_substantiator_from_paths(
            args.main_document_path, args.supporting_documents
        )
    )
    print("Result state:")
    print(result_state)
