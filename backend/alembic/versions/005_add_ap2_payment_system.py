"""Add AP2 agentic payment system tables

Revision ID: 005
Revises: 004
Create Date: 2026-03-15 15:00:00.000000

Adds three tables for the AP2-inspired agentic payment integration:
  - payment_mandates: user's pre-authorized spending limits + payment method
  - agent_orders: orders placed by the AI agent on behalf of the user
  - order_items: line items within each agent order
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. payment_mandates — one per user, upsert-style
    op.create_table(
        "payment_mandates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=False, unique=True),
        sa.Column("payment_method", sa.String(), nullable=False),
        sa.Column("spending_limit", sa.Float(), nullable=False, server_default="500.0"),
        sa.Column("preferred_store_ids", sa.Text(), nullable=True),
        sa.Column("auto_buy_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_payment_mandates_user_id", "payment_mandates", ["user_id"], unique=True)

    # 2. agent_orders — AI-placed orders
    op.create_table(
        "agent_orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("payment_mandate_id", sa.Integer(), nullable=True),
        sa.Column("store_id", sa.String(), nullable=False),
        sa.Column("store_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending_confirmation"),
        sa.Column("subtotal", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("delivery_fee", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("payment_method", sa.String(), nullable=False),
        sa.Column("chat_session_id", sa.Integer(), nullable=True),
        sa.Column("transaction_id", sa.String(), nullable=True),
        sa.Column("intent_description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_mandate_id"], ["payment_mandates.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_agent_orders_user_id", "agent_orders", ["user_id"])
    op.create_index("ix_agent_orders_status", "agent_orders", ["status"])

    # 3. order_items — line items within each agent order
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("product_name", sa.String(), nullable=False),
        sa.Column("product_emoji", sa.String(), nullable=False, server_default="🛒"),
        sa.Column("unit", sa.String(), nullable=False, server_default="phan"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("subtotal", sa.Float(), nullable=False, server_default="0.0"),
        sa.ForeignKeyConstraint(["order_id"], ["agent_orders.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_agent_orders_status", table_name="agent_orders")
    op.drop_index("ix_agent_orders_user_id", table_name="agent_orders")
    op.drop_table("agent_orders")
    op.drop_index("ix_payment_mandates_user_id", table_name="payment_mandates")
    op.drop_table("payment_mandates")
