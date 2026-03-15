"""Add custom_personas table

Revision ID: 004
Revises: 003
Create Date: 2026-03-15 14:00:00.000000

Allows users to create and manage their own AI persona templates.
Backward-compatible — system personas from JSON files are unaffected.
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "custom_personas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(), nullable=False, unique=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("icon", sa.String(), nullable=False, server_default="👨‍🍳"),
        sa.Column("color", sa.String(), nullable=False, server_default="#6B7280"),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("recipe_prefix", sa.Text(), nullable=False, server_default=""),
        sa.Column("meal_plan_prefix", sa.Text(), nullable=False, server_default=""),
        sa.Column("cuisine_filters", sa.Text(), nullable=True, server_default="[]"),
        sa.Column("quick_actions", sa.Text(), nullable=True, server_default="[]"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_custom_personas_slug", "custom_personas", ["slug"])
    op.create_index("ix_custom_personas_created_by", "custom_personas", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_custom_personas_created_by", table_name="custom_personas")
    op.drop_index("ix_custom_personas_slug", table_name="custom_personas")
    op.drop_table("custom_personas")
