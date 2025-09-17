import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from api.upload import convert_uploaded_files_to_file_document
from lib.workflows.claim_substantiation.runner import run_claim_substantiator
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.services.file import FileDocument
from lib.agents.reference_extractor import BibliographyItem
from api.services.chunk_reevaluation import ChunkReevaluationService

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


@app.post("/api/run-claim-substantiation")
async def run_claim_substantiation_workflow(
    main_document: UploadFile = File(...),
    supporting_documents: Optional[list[UploadFile]] = File(default=None),
    use_toulmin: bool = True,
):
    """
    Run the claim substantiation workflow on uploaded documents.

    Args:
        main_document: The main document to analyze for claims
        supporting_documents: Optional supporting documents for substantiation

    Returns:
        The workflow state containing claims, citations, references, and substantiations
    """

    try:
        [main_file, *supporting_files] = await convert_uploaded_files_to_file_document(
            [main_document] + (supporting_documents or [])
        )

        # Run the workflow
        result_state = await run_claim_substantiator(
            file=main_file,
            supporting_files=supporting_files if supporting_files else None,
            use_toulmin=use_toulmin,
        )

        return ClaimSubstantiatorState(**result_state)

    except Exception as e:
        logger.error(f"Error processing workflow: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing workflow: {str(e)}"
        )


# Request/Response models for chunk re-evaluation
class AgentType(BaseModel):
    """Enum-like model for supported agent types"""
    CLAIMS: str = "claims"
    CITATIONS: str = "citations"
    SUBSTANTIATION: str = "substantiation"


class ChunkReevaluationRequest(BaseModel):
    """Request model for re-evaluating a specific chunk"""
    chunk_index: int = Field(
        ge=0, description="Zero-based index of the chunk to re-evaluate"
    )
    agents_to_run: List[str] = Field(
        description="List of agent types to run on the chunk",
        example=["claims", "citations"]
    )
    original_state: Dict[str, Any] = Field(
        description="The original workflow state containing the document and chunks"
    )


class ChunkReevaluationResponse(BaseModel):
    """Response model for chunk re-evaluation results"""
    chunk_index: int = Field(description="The index of the re-evaluated chunk")
    chunk_content: str = Field(description="The content of the re-evaluated chunk")
    updated_results: Dict[str, Any] = Field(
        description="Updated results for the chunk, keyed by agent type"
    )
    agents_run: List[str] = Field(
        description="List of agents that were successfully run on the chunk"
    )
    processing_time_ms: Optional[float] = Field(
        description="Time taken to process the chunk in milliseconds", default=None
    )


@app.post("/api/reevaluate-chunk", response_model=ChunkReevaluationResponse)
async def reevaluate_chunk(request: ChunkReevaluationRequest):
    """
    Re-evaluate a specific chunk with selected agents.

    Args:
        request: Contains chunk index, agents to run, and original state

    Returns:
        Updated results for the specified chunk
    """
    try:
        service = ChunkReevaluationService()
        result = await service.reevaluate_chunk(
            chunk_index=request.chunk_index,
            agents_to_run=request.agents_to_run,
            original_state=request.original_state
        )
        return result
    
    except ValueError as e:
        logger.error(f"Invalid request for chunk re-evaluation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error re-evaluating chunk: {str(e)}")
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
    service = ChunkReevaluationService()
    return {
        "supported_agents": service.get_supported_agents(),
        "agent_descriptions": {
            "claims": "Detect and extract claims from text chunks",
            "citations": "Detect and extract citations from text chunks"
        }
    }
