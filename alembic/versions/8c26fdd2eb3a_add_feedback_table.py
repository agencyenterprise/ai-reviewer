"""add_feedback_table

Revision ID: 8c26fdd2eb3a
Revises: e02d6d007602
Create Date: 2025-10-23 19:19:21.063621

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8c26fdd2eb3a"
down_revision: Union[str, None] = "e02d6d007602"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum("THUMBS_UP", "THUMBS_DOWN", name="feedbacktype").create(op.get_bind())
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_path", postgresql.JSONB(), nullable=False),
        sa.Column(
            "feedback_type",
            postgresql.ENUM(
                "THUMBS_UP", "THUMBS_DOWN", name="feedbacktype", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("feedback_text", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_feedback_workflow_run_id", "feedback", ["workflow_run_id"])
    op.create_index(
        "ix_feedback_entity_path",
        "feedback",
        ["entity_path"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_feedback_entity_path", "feedback")
    op.drop_index("ix_feedback_workflow_run_id", "feedback")
    op.drop_table("feedback")
    sa.Enum("THUMBS_UP", "THUMBS_DOWN", name="feedbacktype").drop(op.get_bind())
