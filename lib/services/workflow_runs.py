import logging
from typing import List, Optional
from fastapi import HTTPException
from langgraph.types import StateSnapshot
from pydantic import BaseModel
from lib.config.database import get_db
from lib.models.workflow_run import WorkflowRun
from lib.workflows.claim_substantiation.checkpointer import get_checkpointer
from lib.workflows.claim_substantiation.graph import build_claim_substantiator_graph
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


class WorkflowRunDetailed(BaseModel):
    run: WorkflowRun
    state: Optional[ClaimSubstantiatorState] = None


def _convert_state_snapshot(state_snapshot: StateSnapshot) -> ClaimSubstantiatorState:
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
