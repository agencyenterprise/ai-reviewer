import logging
import uuid
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import build_config_from_form
from api.upload import convert_uploaded_files_to_file_document
from lib.agents.registry import agent_registry
from lib.models.workflow_run import WorkflowRun
from lib.services.eval_generator.generator import (
    ChunkEvalPackageRequest,
    ClaimSubstantiatorState,
    EvalPackageRequest,
    eval_test_generator,
)
from lib.services.workflow_runs import (
    WorkflowRunDetailed,
    get_workflow_run_detailed,
    get_workflow_runs,
)
from lib.workflows.claim_substantiation.runner import (
    reevaluate_single_chunk,
    run_claim_substantiator,
)
from lib.workflows.claim_substantiation.state import (
    ChunkReevaluationRequest,
    ChunkReevaluationResponse,
    SubstantiationWorkflowConfig,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Analyst API")


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
    config: SubstantiationWorkflowConfig = Depends(build_config_from_form),
):
    """
    Run the claim substantiation workflow on uploaded documents.

    Args:
        main_document: The main document to analyze for claims
        supporting_documents: Optional supporting documents for substantiation
        config: Workflow configuration built from form fields

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
            config=config,
        )

        return result_state

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

        config_overrides = (
            SubstantiationWorkflowConfig(
                session_id=request.session_id or str(uuid.uuid4())
            )
            if request.session_id
            else None
        )

        updated_state = await reevaluate_single_chunk(
            original_result=request.original_state,
            chunk_index=request.chunk_index,
            agents_to_run=request.agents_to_run,
            config_overrides=config_overrides,
        )

        processing_time_ms = (time.time() - start_time) * 1000

        return ChunkReevaluationResponse(
            state=updated_state,
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


@app.post("/api/generate-eval-package")
async def generate_eval_package(request: EvalPackageRequest):
    """
    Generate complete eval test package as downloadable zip.

    Args:
        request: Contains analysis results and metadata for test generation

    Returns:
        Zip file containing YAML test files and data files
    """
    try:
        return eval_test_generator.generate_package(
            results=request.results,
            test_name=request.test_name,
            description=request.description,
        )

    except Exception as e:
        logger.error(f"Error generating eval package: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error generating eval package: {str(e)}"
        )


@app.post("/api/generate-chunk-eval-package")
async def generate_chunk_eval_package(request: ChunkEvalPackageRequest):
    """
    Generate eval test package for a specific chunk with selected agents.
    Only includes files required by the selected agents.

    Args:
        request: Contains analysis results, chunk index, selected agents, and metadata

    Returns:
        Optimized zip file containing only necessary YAML test files and data files
    """
    try:
        return eval_test_generator.generate_chunk_package(
            results=request.results,
            chunk_index=request.chunk_index,
            selected_agents=request.selected_agents,
            test_name=request.test_name,
            description=request.description,
        )

    except ValueError as e:
        logger.error(f"Invalid request for chunk eval generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating chunk eval package: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error generating chunk eval package: {str(e)}"
        )


@app.get("/api/workflow-runs", response_model=List[WorkflowRun])
async def list_workflow_runs():
    return await get_workflow_runs()


@app.get("/api/workflow-run/{workflow_run_id}", response_model=WorkflowRunDetailed)
async def get_workflow_run(workflow_run_id: str):
    return await get_workflow_run_detailed(workflow_run_id)
