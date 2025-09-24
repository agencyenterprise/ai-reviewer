import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from api.upload import convert_uploaded_files_to_file_document
from lib.workflows.claim_substantiation.runner import (
    run_claim_substantiator,
    reevaluate_single_chunk,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    ChunkReevaluationRequest,
    ChunkReevaluationResponse,
    ClaimSubstantiationChunk,
)
from lib.services.file import FileDocument
from lib.agents.reference_extractor import BibliographyItem
from lib.agents.registry import agent_registry

logger = logging.getLogger(__name__)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to only our own origin later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def read_health():
    return {"status": "healthy"}


@app.post("/api/run-claim-substantiation", response_model=ClaimSubstantiatorState)
async def run_claim_substantiation_workflow(
    main_document: UploadFile = File(...),
    supporting_documents: Optional[list[UploadFile]] = File(default=None),
    use_toulmin: bool = True,
    domain: Optional[str] = None,
    target_audience: Optional[str] = None,
):
    """
    Run the claim substantiation workflow on uploaded documents.

    Args:
        main_document: The main document to analyze for claims
        supporting_documents: Optional supporting documents for substantiation
        use_toulmin: Whether to use Toulmin claim detection (default: True)
        domain: Optional domain context for more accurate analysis
        target_audience: Optional target audience context for analysis

    Returns:
        The workflow state containing claims, citations, references, and substantiations
    """

    try:
        [main_file, *supporting_files] = await convert_uploaded_files_to_file_document(
            [main_document] + (supporting_documents or [])
        )

        result_state = await run_claim_substantiator(
            file=main_file,
            supporting_files=supporting_files if supporting_files else None,
            use_toulmin=use_toulmin,
            domain=domain,
            target_audience=target_audience,
        )

        return ClaimSubstantiatorState(**result_state)

    except Exception as e:
        logger.error(f"Error processing workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing workflow: {str(e)}"
        )


@app.post("/api/reevaluate-chunk", response_model=ChunkReevaluationResponse)
async def reevaluate_chunk(request: ChunkReevaluationRequest):
    """
    Re-evaluate a specific chunk with selected agents using unified LangGraph workflow.

    Args:
        request: Contains chunk index, agents to run, and original state

    Returns:
        Updated results for the specified chunk
    """
    try:
        agent_registry.validate_agents(request.agents_to_run)

        import time

        start_time = time.time()

        updated_chunk = await reevaluate_single_chunk(
            original_result=request.original_state,
            chunk_index=request.chunk_index,
            agents_to_run=request.agents_to_run,
        )

        processing_time_ms = (time.time() - start_time) * 1000

        return ChunkReevaluationResponse(
            chunk=updated_chunk,
            agents_run=request.agents_to_run,
            processing_time_ms=processing_time_ms,
        )

    except ValueError as e:
        logger.error(f"Invalid request for chunk re-evaluation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error re-evaluating chunk: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error re-evaluating chunk: {str(e)}"
        )


@app.get("/api/supported-agents")
async def get_supported_agents():
    """
    Get list of supported agent types for chunk re-evaluation.

    Returns:
        List of supported agent type strings
    """
    return {
        "supported_agents": agent_registry.get_supported_types(),
        "agent_descriptions": agent_registry.get_agent_descriptions(),
    }
