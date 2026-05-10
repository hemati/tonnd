"""Add FatSecret integration: food_entries table + user OAuth1 token columns.

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-05-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "g7h8i9j0k1l2"
down_revision = "f6g7h8i9j0k1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- user: FatSecret OAuth1 token columns (Fernet-encrypted at rest) ---
    op.add_column("user", sa.Column("fatsecret_oauth_token", sa.Text(), nullable=True))
    op.add_column("user", sa.Column("fatsecret_oauth_token_secret", sa.Text(), nullable=True))

    # --- food_entries (per-meal entries from FatSecret food diary) ---
    op.create_table(
        "food_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("meal", sa.String(32), nullable=True),
        sa.Column("food_id", sa.String(64), nullable=True),
        sa.Column("serving_id", sa.String(64), nullable=True),
        sa.Column("food_entry_name", sa.String(256), nullable=False),
        sa.Column("food_entry_description", sa.String(512), nullable=True),
        sa.Column("number_of_units", sa.Float(), nullable=True),
        # Macros
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("carbs_g", sa.Float(), nullable=True),
        sa.Column("fat_g", sa.Float(), nullable=True),
        sa.Column("protein_g", sa.Float(), nullable=True),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("sugar_g", sa.Float(), nullable=True),
        sa.Column("saturated_fat_g", sa.Float(), nullable=True),
        sa.Column("polyunsaturated_fat_g", sa.Float(), nullable=True),
        sa.Column("monounsaturated_fat_g", sa.Float(), nullable=True),
        # Micros
        sa.Column("cholesterol_mg", sa.Float(), nullable=True),
        sa.Column("sodium_mg", sa.Float(), nullable=True),
        sa.Column("calcium_mg", sa.Float(), nullable=True),
        sa.Column("iron_mg", sa.Float(), nullable=True),
        sa.Column("potassium_mg", sa.Float(), nullable=True),
        sa.Column("vitamin_a_iu", sa.Float(), nullable=True),
        sa.Column("vitamin_c_mg", sa.Float(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "source", "external_id", name="uq_food_entry"),
    )
    op.create_index("ix_food_entry_user_date", "food_entries", ["user_id", "date"])


def downgrade() -> None:
    op.drop_index("ix_food_entry_user_date", table_name="food_entries")
    op.drop_table("food_entries")
    op.drop_column("user", "fatsecret_oauth_token_secret")
    op.drop_column("user", "fatsecret_oauth_token")
