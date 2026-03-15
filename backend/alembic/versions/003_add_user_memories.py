"""Add user_memories table

Revision ID: 003
Revises: 002
Create Date: 2026-03-15 12:00:00.000000

Stores factual, auto-extracted information about users (allergies, preferences,
goals, constraints). Backward-compatible — users without rows get no memory
context, which is functionally equivalent to the old behaviour.
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_memories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("source", sa.String(), nullable=False, server_default="inferred"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    # Fast lookup: fetch all memories for a user
    op.create_index("ix_user_memories_user_id", "user_memories", ["user_id"])
    # Prevent duplicates: same fact won't be stored twice
    op.create_unique_constraint(
        "uq_user_memory_entry",
        "user_memories",
        ["user_id", "category", "key", "value"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_memory_entry", "user_memories", type_="unique")
    op.drop_index("ix_user_memories_user_id", table_name="user_memories")
    op.drop_table("user_memories")
