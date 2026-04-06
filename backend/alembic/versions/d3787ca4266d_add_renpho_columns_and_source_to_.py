"""add renpho columns and source to fitness metrics

Revision ID: d3787ca4266d
Revises:
Create Date: 2026-04-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd3787ca4266d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User table: add Renpho fields (IF NOT EXISTS for idempotency)
    op.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS renpho_email TEXT DEFAULT NULL')
    op.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS renpho_session_key TEXT DEFAULT NULL')

    # FitnessMetric: add source column
    op.execute("ALTER TABLE fitness_metrics ADD COLUMN IF NOT EXISTS source VARCHAR(16) NOT NULL DEFAULT 'fitbit'")

    # Update unique constraint — drop old if exists, create new
    op.execute("ALTER TABLE fitness_metrics DROP CONSTRAINT IF EXISTS uq_user_date_metric")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_user_date_metric_source') THEN
                ALTER TABLE fitness_metrics ADD CONSTRAINT uq_user_date_metric_source
                    UNIQUE (user_id, date, metric_type, source);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE fitness_metrics DROP CONSTRAINT IF EXISTS uq_user_date_metric_source")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_user_date_metric') THEN
                ALTER TABLE fitness_metrics ADD CONSTRAINT uq_user_date_metric
                    UNIQUE (user_id, date, metric_type);
            END IF;
        END $$;
    """)
    op.execute("ALTER TABLE fitness_metrics DROP COLUMN IF EXISTS source")
    op.execute('ALTER TABLE "user" DROP COLUMN IF EXISTS renpho_session_key')
    op.execute('ALTER TABLE "user" DROP COLUMN IF EXISTS renpho_email')
