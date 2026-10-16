"""drop app configs

Revision ID: cc30d374666d
Revises: 7a8e44e902a7
Create Date: 2026-10-16 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc30d374666d'
down_revision: Union[str, None] = '7a8e44e902a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_app_configs_key'), table_name='app_configs')
    op.drop_table('app_configs')


def downgrade() -> None:
    op.create_table('app_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('key', sa.String(), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_app_configs_key'), 'app_configs', ['key'], unique=True)
