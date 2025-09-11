import os
import tempfile
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from lib.workflows.claim_substantiation.runner import run_claim_substantiator
from lib.services.file import File as WorkflowFile

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

            return JSONResponse(
                content={
                    "message": "Workflow completed",
                    "markdown": await main_file.get_markdown(),
                }
            )

            # # Run the workflow
            # result_state = await run_claim_substantiator(
            #     file=main_file,
            #     supporting_files=supporting_files if supporting_files else None,
            # )

            # # Convert the state to a JSON-serializable format
            # serializable_state = {
            #     # "file_name": main_file.file_name,
            #     # "file_type": main_file.file_type,
            #     # "supporting_files": [
            #     #     {"file_name": f.file_name, "file_type": f.file_type}
            #     #     for f in supporting_files
            #     # ],
            #     "claims_by_chunk": result_state.get("claims_by_chunk", []),
            #     "citations_by_chunk": result_state.get("citations_by_chunk", []),
            #     "references": result_state.get("references", []),
            #     "matches": result_state.get("matches", []),
            #     "claim_substantiations_by_chunk": result_state.get(
            #         "claim_substantiations_by_chunk", []
            #     ),
            # }

            # return JSONResponse(content=serializable_state)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing workflow: {str(e)}"
        )
