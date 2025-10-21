import logging
from typing import List, Optional
from fastapi import HTTPException
from langgraph.types import StateSnapshot
from pydantic import BaseModel
from lib.config.database import get_db
from lib.models.workflow_run import WorkflowRun, WorkflowRunStatus
from lib.workflows.claim_substantiation.checkpointer import get_checkpointer
from lib.workflows.claim_substantiation.graph import build_claim_substantiator_graph
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


class WorkflowRunDetailed(BaseModel):
    run: WorkflowRun
    state: Optional[ClaimSubstantiatorState] = None


def _convert_state_snapshot(
    state_snapshot: StateSnapshot,
) -> Optional[ClaimSubstantiatorState]:
    try:
        return ClaimSubstantiatorState(**state_snapshot.values)
    except Exception as e:
        logger.warning(
            f"Error converting state snapshot for thread {state_snapshot.config['configurable']['thread_id']} (possibly an old state schema version): {e}"
        )
        return None


async def get_workflow_run_detailed(id: str) -> WorkflowRunDetailed:
    with get_db() as db:
        run = db.query(WorkflowRun).filter(WorkflowRun.id == id).first()

    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    graph = build_claim_substantiator_graph()

    async with get_checkpointer() as checkpointer:
        app = graph.compile(checkpointer=checkpointer)
        state = await app.aget_state(
            {"configurable": {"thread_id": run.langgraph_thread_id}}
        )

    return WorkflowRunDetailed(run=run, state=_convert_state_snapshot(state))


async def get_workflow_runs() -> List[WorkflowRun]:
    with get_db() as db:
        runs = (
            db.query(WorkflowRun)
            .order_by(WorkflowRun.created_at.desc())
            .limit(100)
            .all()
        )

    return runs


async def upsert_workflow_run(
    session_id: str,
    status: WorkflowRunStatus,
    title: Optional[str] = None,
) -> Optional[str]:
    """
    Create or update a workflow run using the session_id as the key.

    This is the single function for all workflow run database operations.
    It handles both creation (when no run exists) and updates (when it does).

    Args:
        session_id: The LangGraph thread ID (unique identifier)
        status: The workflow status to set
        title: Optional title to set/update

    Returns:
        The workflow run UUID as a string, or None if session_id is not provided
    """
    if not session_id:
        logger.warning("upsert_workflow_run: No session_id provided")
        return None

    with get_db() as db:
        run = (
            db.query(WorkflowRun)
            .filter(WorkflowRun.langgraph_thread_id == session_id)
            .first()
        )

        if run is None:
            # Create new run
            run = WorkflowRun(
                langgraph_thread_id=session_id,
                title=title or "Untitled",
                status=status,
            )
            db.add(run)
        else:
            # Update existing run
            run.status = status
            if title:
                run.title = title

        db.commit()
        db.refresh(run)
        return str(run.id)


def get_workflow_run_id_by_session(session_id: str) -> Optional[str]:
    """
    Get the workflow run ID for a given session ID.

    Args:
        session_id: The LangGraph thread ID

    Returns:
        The workflow run UUID as a string, or None if not found
    """
    if not session_id:
        return None

    with get_db() as db:
        run = (
            db.query(WorkflowRun)
            .filter(WorkflowRun.langgraph_thread_id == session_id)
            .first()
        )
        return str(run.id) if run else None


async def delete_workflow_run(workflow_run_id: str) -> None:
    with get_db() as db:
        run = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_run_id).first()

        if run is None:
            raise HTTPException(status_code=404, detail="Workflow run not found")

        thread_id = run.langgraph_thread_id

        db.delete(run)
        db.commit()

    try:
        async with get_checkpointer() as checkpointer:
            async with checkpointer.conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM checkpoints WHERE thread_id = %s",
                    (thread_id,),
                )
                await cur.execute(
                    "DELETE FROM checkpoint_writes WHERE thread_id = %s",
                    (thread_id,),
                )
    except Exception as e:
        logger.error(f"Error deleting checkpoints for thread {thread_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting checkpoint data: {str(e)}"
        )
