"""add is_sellable and base_price to course

Revision ID: 844c4ff16afe
Revises: 003
Create Date: 2026-07-23 16:39:16.151794
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '844c4ff16afe'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('training_courses', sa.Column('is_sellable', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('training_courses', sa.Column('base_price', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False))


def downgrade() -> None:
    op.drop_column('training_courses', 'base_price')
    op.drop_column('training_courses', 'is_sellable')
