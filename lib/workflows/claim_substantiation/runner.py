# Convenience helpers
from typing import List, Optional
from lib.services.file import File
from lib.workflows.claim_substantiation.graph import build_claim_substantiator_graph
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState


async def run_claim_substantiator(
    file: File, supporting_files: Optional[List[File]] = None
) -> ClaimSubstantiatorState:
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

    return await run_claim_substantiator(file, supporting_files)


if __name__ == "__main__":
    import argparse
    import asyncio
    from pathlib import Path

    data_dir = Path(__file__).parent.parent.parent.parent / "tests" / "data"
    print(data_dir)
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
