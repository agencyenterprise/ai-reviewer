"""Initial migration: create agents, workflows, workflow_runs, chats tables

Revision ID: e8cd4f1f7766
Revises: 
Create Date: 2025-09-09 16:55:43.302893

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e8cd4f1f7766"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agents table
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("model", sa.String(255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column(
            "mandatory_tools", postgresql.ARRAY(sa.String()), server_default="{}"
        ),
        sa.Column(
            "disallowed_tools", postgresql.ARRAY(sa.String()), server_default="{}"
        ),
        sa.Column(
            "dependencies", postgresql.ARRAY(postgresql.UUID()), server_default="{}"
        ),
        sa.Column("output_schema", sa.JSON()),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Create workflows table
    op.create_table(
        "workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("stages", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Create workflow_runs table
    op.create_table(
        "workflow_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stages", sa.JSON(), nullable=False),
        sa.Column("chat_ids", sa.JSON()),
        sa.Column("chat_results", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
    )

    # Create chats table
    op.create_table(
        "chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("history", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
    )


def downgrade() -> None:
    # Drop tables in reverse order to handle foreign key dependencies
    op.drop_table("chats")
    op.drop_table("workflow_runs")
    op.drop_table("workflows")
    op.drop_table("agents")
