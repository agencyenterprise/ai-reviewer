"""
Feedback service layer.

Provides business logic for feedback CRUD operations using coordinate-based addressing.
"""

from typing import Optional
import uuid

from lib.models.feedback import Feedback, FeedbackType


def create_or_update_claim_feedback(
    session,
    workflow_run_id: uuid.UUID,
    chunk_index: int,
    claim_index: int,
    feedback_type: FeedbackType,
    feedback_text: Optional[str] = None,
) -> Feedback:
    """
    Create or update feedback for a specific claim.

    If feedback already exists for this claim, it will be updated.
    Otherwise, a new feedback entry is created.
    """
    entity_path = {"chunk_index": chunk_index, "claim_index": claim_index}

    existing_feedback = (
        session.query(Feedback)
        .filter(Feedback.workflow_run_id == workflow_run_id)
        .filter(Feedback.entity_path == entity_path)
        .first()
    )

    if existing_feedback:
        existing_feedback.feedback_type = feedback_type
        existing_feedback.feedback_text = feedback_text
        session.add(existing_feedback)
        session.commit()
        session.refresh(existing_feedback)
        return existing_feedback

    feedback = Feedback.for_claim(
        workflow_run_id=workflow_run_id,
        chunk_index=chunk_index,
        claim_index=claim_index,
        feedback_type=feedback_type,
        feedback_text=feedback_text,
    )

    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def get_claim_feedback(
    session, workflow_run_id: uuid.UUID, chunk_index: int, claim_index: int
) -> Optional[Feedback]:
    """Get feedback for a specific claim"""
    entity_path = {"chunk_index": chunk_index, "claim_index": claim_index}

    return (
        session.query(Feedback)
        .filter(Feedback.workflow_run_id == workflow_run_id)
        .filter(Feedback.entity_path == entity_path)
        .first()
    )


def get_workflow_feedback(session, workflow_run_id: uuid.UUID) -> list[Feedback]:
    """Get all feedback for a workflow run"""
    return (
        session.query(Feedback)
        .filter(Feedback.workflow_run_id == workflow_run_id)
        .all()
    )


def delete_feedback(session, feedback_id: uuid.UUID) -> bool:
    """Delete feedback by ID"""
    feedback = session.query(Feedback).filter(Feedback.id == feedback_id).first()
    if feedback:
        session.delete(feedback)
        session.commit()
        return True
    return False
