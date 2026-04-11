"""add hevy_api_key to user

Revision ID: a1b2c3d4e5f6
Revises: d3787ca4266d
Create Date: 2026-04-11

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd3787ca4266d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS hevy_api_key TEXT DEFAULT NULL')


def downgrade() -> None:
    op.execute('ALTER TABLE "user" DROP COLUMN IF EXISTS hevy_api_key')
