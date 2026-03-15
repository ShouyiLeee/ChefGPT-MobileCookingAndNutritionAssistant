"""AP2-inspired agentic payment models — PaymentMandate, AgentOrder, OrderItem."""
from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class PaymentMandate(SQLModel, table=True):
    """
    User's pre-authorized spending mandate (AP2 Payment Mandate concept).
    One mandate per user — upsert-style. Stores spending limit and preferred
    payment method so the AI agent can place orders without per-transaction approval.
    """

    __tablename__ = "payment_mandates"

    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, index=True)
    payment_method: str = Field(nullable=False)  # "cod"|"momo"|"zalopay"|"bank_transfer"
    spending_limit: float = Field(default=500.0)  # max per transaction, in k VND
    preferred_store_ids: Optional[str] = None  # JSON array e.g. '["bhx","winmart"]'
    auto_buy_enabled: bool = Field(default=False)  # future: skip confirmation
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Relationships
    orders: List["AgentOrder"] = Relationship(back_populates="mandate")


class AgentOrder(SQLModel, table=True):
    """
    An order placed by the AI agent on behalf of the user (AP2 Cart Mandate execution).
    Tracks full lifecycle: pending_confirmation → confirmed → paid → delivered.
    """

    __tablename__ = "agent_orders"

    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    payment_mandate_id: Optional[int] = Field(
        foreign_key="payment_mandates.id", default=None
    )
    store_id: str = Field(nullable=False)    # "bhx"|"winmart"|"coopmart"|"lotte"|"bigc"
    store_name: str = Field(nullable=False)
    status: str = Field(
        default="pending_confirmation"
    )  # pending_confirmation|confirmed|paid|delivered|cancelled
    subtotal: float = Field(default=0.0)
    delivery_fee: float = Field(default=0.0)
    total: float = Field(default=0.0)
    payment_method: str = Field(nullable=False)  # copied from mandate at order time
    chat_session_id: Optional[int] = Field(
        foreign_key="chat_sessions.id", default=None
    )
    transaction_id: Optional[str] = None   # "mock_txn_xxxxxxxx"
    intent_description: Optional[str] = None  # what the user asked for
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Relationships
    mandate: Optional[PaymentMandate] = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    """Line item within an AgentOrder."""

    __tablename__ = "order_items"

    id: int = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="agent_orders.id", index=True)
    product_id: str = Field(nullable=False)   # e.g. "b1", "w4" from product catalog
    product_name: str = Field(nullable=False)
    product_emoji: str = Field(default="🛒")
    unit: str = Field(default="phần")
    quantity: int = Field(default=1)
    unit_price: float = Field(default=0.0)   # in k VND
    subtotal: float = Field(default=0.0)

    # Relationships
    order: Optional[AgentOrder] = Relationship(back_populates="items")
