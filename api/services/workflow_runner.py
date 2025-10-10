"""
Background workflow execution service
"""

import logging

from lib.config.database import get_db
from lib.models.workflow_run import WorkflowRun, WorkflowRunStatus
from lib.services.file import FileDocument
from lib.workflows.claim_substantiation.runner import run_claim_substantiator
from lib.workflows.claim_substantiation.state import SubstantiationWorkflowConfig

logger = logging.getLogger(__name__)


async def run_workflow_background(
    main_file: FileDocument,
    supporting_files: list[FileDocument] | None,
    config: SubstantiationWorkflowConfig,
) -> None:
    """
    Background task to run the claim substantiation workflow.

    Updates workflow status from PENDING -> RUNNING -> COMPLETED.
    """
    try:
        logger.info(
            f"Starting background workflow execution for session {config.session_id}"
        )

        with get_db() as db:
            workflow_run = (
                db.query(WorkflowRun)
                .filter(WorkflowRun.langgraph_thread_id == config.session_id)
                .first()
            )
            if workflow_run:
                workflow_run.status = WorkflowRunStatus.RUNNING
                db.commit()

        await run_claim_substantiator(
            file=main_file,
            supporting_files=supporting_files,
            config=config,
        )

        with get_db() as db:
            workflow_run = (
                db.query(WorkflowRun)
                .filter(WorkflowRun.langgraph_thread_id == config.session_id)
                .first()
            )
            if workflow_run:
                workflow_run.status = WorkflowRunStatus.COMPLETED
                db.commit()

        logger.info(f"Background workflow completed for session {config.session_id}")

    except Exception as e:
        logger.error(f"Error in background workflow: {str(e)}", exc_info=True)
