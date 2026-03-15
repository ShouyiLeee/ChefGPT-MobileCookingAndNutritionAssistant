"""Pydantic schemas for AP2 agentic payment system."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Mandate Schemas ────────────────────────────────────────────────────────────

class PaymentMandateCreate(BaseModel):
    """Request body for POST /payment-mandate (create or update user's mandate)."""
    payment_method: str = Field(
        ...,
        description="cod | momo | zalopay | bank_transfer",
    )
    spending_limit: float = Field(
        default=500.0,
        ge=50.0,
        le=5000.0,
        description="Maximum spend per transaction in k VND",
    )
    preferred_store_ids: Optional[List[str]] = Field(
        default=None,
        description="Store IDs the agent is allowed to order from",
    )
    auto_buy_enabled: bool = Field(
        default=False,
        description="Future: allow agent to order without confirmation",
    )


class PaymentMandateResponse(BaseModel):
    """Response for GET/POST /payment-mandate."""
    id: int
    payment_method: str
    spending_limit: float
    preferred_store_ids: List[str]
    auto_buy_enabled: bool
    is_active: bool


# ── Cart Mandate Schemas (AP2 Cart Mandate concept) ────────────────────────────

class CartMandateItemSchema(BaseModel):
    """Single item in a Cart Mandate."""
    product_id: str
    product_name: str
    product_emoji: str
    unit: str
    quantity: int = Field(ge=1)
    unit_price: float
    subtotal: float


class CartMandateSchema(BaseModel):
    """AP2 Cart Mandate — what the agent wants to buy."""
    store_id: str
    store_name: str
    items: List[CartMandateItemSchema]
    subtotal: float
    delivery_fee: float
    estimated_total: float
    intent_description: str = ""


# ── Shopping Suggestion (injected into chat response) ─────────────────────────

class ShoppingSuggestionSchema(BaseModel):
    """
    Embedded in ChatMessageResponse when the AI detects a shopping intent.
    The Flutter app renders this as an _AgentShoppingCard in the chat bubble.
    """
    cart_mandate: CartMandateSchema
    estimated_total: float
    requires_confirmation: bool = True
    mandate_id: Optional[int] = Field(
        default=None,
        description="User's active mandate ID; null means no mandate configured yet",
    )


# ── Purchase Confirmation ──────────────────────────────────────────────────────

class ConfirmPurchaseRequest(BaseModel):
    """Request body for POST /chat/confirm-purchase."""
    cart_mandate: CartMandateSchema
    payment_mandate_id: Optional[int] = Field(
        default=None,
        description="Explicit mandate ID; if null, uses user's active mandate",
    )


class ConfirmPurchaseResponse(BaseModel):
    """Response for POST /chat/confirm-purchase."""
    order_id: int
    status: str
    total: float
    store_name: str
    estimated_delivery: str
    transaction_id: str


# ── Order Schemas ──────────────────────────────────────────────────────────────

class OrderItemResponse(BaseModel):
    """Single item in an AgentOrderResponse."""
    product_id: str
    product_name: str
    product_emoji: str
    quantity: int
    unit: str
    unit_price: float
    subtotal: float


class AgentOrderResponse(BaseModel):
    """Response for GET /orders and GET /orders/{id}."""
    id: int
    store_id: str
    store_name: str
    status: str
    subtotal: float
    delivery_fee: float
    total: float
    payment_method: str
    transaction_id: Optional[str]
    intent_description: Optional[str]
    items: List[OrderItemResponse]
    created_at: datetime
