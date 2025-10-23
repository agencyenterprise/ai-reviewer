"""
Feedback API endpoints.

Provides RESTful API for managing user feedback on analysis results.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from lib.config.database import get_db
from lib.models.feedback import Feedback, FeedbackType
from lib.services import feedback_service

router = APIRouter(tags=["feedback"])


class ClaimFeedbackRequest(BaseModel):
    """Request model for claim feedback"""

    workflow_run_id: UUID
    chunk_index: int = Field(ge=0, description="Zero-based chunk index")
    claim_index: int = Field(ge=0, description="Zero-based claim index within chunk")
    feedback_type: str  # Accept as string, convert in endpoint
    feedback_text: Optional[str] = Field(
        default=None,
        description="Optional feedback text (typically used with thumbs down)",
    )


class FeedbackResponse(BaseModel):
    """Response model for feedback"""

    id: UUID
    workflow_run_id: UUID
    entity_path: dict
    feedback_type: FeedbackType
    feedback_text: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, feedback: Feedback) -> "FeedbackResponse":
        """Convert from Feedback model"""
        return cls(
            id=feedback.id,
            workflow_run_id=feedback.workflow_run_id,
            entity_path=feedback.entity_path,
            feedback_type=feedback.feedback_type,
            feedback_text=feedback.feedback_text,
            created_at=feedback.created_at.isoformat(),
            updated_at=feedback.updated_at.isoformat(),
        )


@router.post("/api/feedback/claim", response_model=FeedbackResponse)
async def submit_claim_feedback(request: ClaimFeedbackRequest) -> FeedbackResponse:
    """Submit or update feedback for a specific claim"""
    with get_db() as session:
        feedback_type = FeedbackType(request.feedback_type)

        feedback = feedback_service.create_or_update_claim_feedback(
            session=session,
            workflow_run_id=request.workflow_run_id,
            chunk_index=request.chunk_index,
            claim_index=request.claim_index,
            feedback_type=feedback_type,
            feedback_text=request.feedback_text,
        )

        return FeedbackResponse.from_model(feedback)


@router.get("/api/feedback/claim", response_model=Optional[FeedbackResponse])
async def get_claim_feedback(
    workflow_run_id: UUID,
    chunk_index: int,
    claim_index: int,
) -> Optional[FeedbackResponse]:
    """Get feedback for a specific claim"""
    with get_db() as session:
        feedback = feedback_service.get_claim_feedback(
            session=session,
            workflow_run_id=workflow_run_id,
            chunk_index=chunk_index,
            claim_index=claim_index,
        )

        if feedback:
            return FeedbackResponse.from_model(feedback)
        return None


@router.get(
    "/api/feedback/workflow/{workflow_run_id}", response_model=list[FeedbackResponse]
)
async def get_workflow_feedback(workflow_run_id: UUID) -> list[FeedbackResponse]:
    """Get all feedback for a workflow run"""
    with get_db() as session:
        feedbacks = feedback_service.get_workflow_feedback(
            session=session, workflow_run_id=workflow_run_id
        )

        return [FeedbackResponse.from_model(f) for f in feedbacks]


@router.delete("/api/feedback/{feedback_id}", response_model=dict)
async def delete_feedback(feedback_id: UUID) -> dict:
    """Delete feedback by ID"""
    with get_db() as session:
        success = feedback_service.delete_feedback(
            session=session, feedback_id=feedback_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="Feedback not found")

        return {"success": True}
