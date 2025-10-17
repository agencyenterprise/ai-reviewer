"""add_pgvector_extension

Revision ID: e02d6d007602
Revises: 98b0e22e71a6
Create Date: 2025-10-17 10:11:39.306576

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "e02d6d007602"
down_revision: Union[str, None] = "98b0e22e71a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE")
