import logging
import os
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from lib.workflows.claim_substantiation.runner import run_claim_substantiator
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.services.file import File as WorkflowFile

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
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save main document
            main_file_path = os.path.join(temp_dir, main_document.filename)
            with open(main_file_path, "wb") as buffer:
                content = await main_document.read()
                buffer.write(content)

            # Create File object for main document
            main_file = WorkflowFile(file_path=main_file_path)

            # Handle supporting documents if provided
            supporting_files = []
            if supporting_documents is not None:
                for supporting_doc in supporting_documents:
                    if supporting_doc.filename:  # Skip empty files
                        supporting_file_path = os.path.join(
                            temp_dir, supporting_doc.filename
                        )
                        with open(supporting_file_path, "wb") as buffer:
                            content = await supporting_doc.read()
                            buffer.write(content)

                        supporting_file = WorkflowFile(file_path=supporting_file_path)
                        supporting_files.append(supporting_file)

            # Run the workflow
            result_state = await run_claim_substantiator(
                file=main_file,
                supporting_files=supporting_files if supporting_files else None,
            )

            return ClaimSubstantiatorState(**result_state)

    except Exception as e:
        logger.error(f"Error processing workflow: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing workflow: {str(e)}"
        )
