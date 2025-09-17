import logging
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.upload import convert_uploaded_files_to_file_document
from lib.workflows.claim_substantiation.runner import run_claim_substantiator
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

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
