"""Add user_persona_settings table

Revision ID: 002
Revises: 001
Create Date: 2026-03-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_persona_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("active_persona_id", sa.String(), nullable=False, server_default="asian_chef"),
        sa.Column("custom_prompt_overrides", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_user_persona_settings_user_id",
        "user_persona_settings",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_persona_settings_user_id", table_name="user_persona_settings")
    op.drop_table("user_persona_settings")
