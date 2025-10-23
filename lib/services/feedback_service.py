"""
Feedback service layer.

Provides business logic for feedback CRUD operations using coordinate-based addressing.
"""

from typing import Optional
import uuid

from lib.models.feedback import Feedback, FeedbackType


def create_feedback(
    session,
    workflow_run_id: uuid.UUID,
    entity_path: dict,
    feedback_type: FeedbackType,
    feedback_text: Optional[str] = None,
) -> Feedback:
    """
    Create new feedback for any entity.

    Args:
        entity_path: Dict with entity coordinates, e.g.:
            - {"chunk_index": 0} for chunk
            - {"chunk_index": 0, "claim_index": 1} for claim
            - {"reference_index": 2} for reference
            - {} for workflow-level feedback
    """
    feedback = Feedback(
        workflow_run_id=workflow_run_id,
        entity_path=entity_path,
        feedback_type=feedback_type,
        feedback_text=feedback_text,
    )

    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def create_or_update_feedback(
    session,
    workflow_run_id: uuid.UUID,
    entity_path: dict,
    feedback_type: FeedbackType,
    feedback_text: Optional[str] = None,
) -> Feedback:
    """
    Create or update feedback for any entity.

    If feedback already exists for this entity, it will be updated.
    Otherwise, a new feedback entry is created.
    """
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

    return create_feedback(
        session=session,
        workflow_run_id=workflow_run_id,
        entity_path=entity_path,
        feedback_type=feedback_type,
        feedback_text=feedback_text,
    )


def get_feedback(
    session, workflow_run_id: uuid.UUID, entity_path: dict
) -> Optional[Feedback]:
    """Get feedback for a specific entity"""
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
