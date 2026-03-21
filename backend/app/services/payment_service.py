"""
PaymentService — AP2-inspired mock payment execution.

Simulates a payment gateway (Stripe sandbox concept) with:
  - Spending limit enforcement (from PaymentMandate)
  - Mock charge with 95% success rate and 0.3s simulated latency
  - AgentOrder + OrderItem persistence in DB

For production: replace _mock_stripe_charge() with real Stripe/MoMo/ZaloPay SDK calls.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import AgentOrder, OrderItem, PaymentMandate
from app.services.shopping_agent import CartMandate


@dataclass
class PaymentResult:
    success: bool
    transaction_id: str
    error_message: Optional[str] = None


@dataclass
class OrderResult:
    order_id: int
    status: str
    total: float
    transaction_id: str


class PaymentService:
    """Singleton service — use the module-level `payment_service` instance."""

    async def execute_payment(
        self,
        user_id: str,
        cart: CartMandate,
        mandate: PaymentMandate,
        db: AsyncSession,
        chat_session_id: Optional[int] = None,
    ) -> OrderResult:
        """
        Execute a payment for the given cart mandate.

        Steps:
          1. Enforce spending limit from mandate
          2. Call mock payment gateway
          3. Persist AgentOrder + OrderItems
          4. Return OrderResult

        Raises:
          ValueError: if cart exceeds spending limit
          RuntimeError: if mock payment fails
        """
        logger.info(
            "payment:execute | user_id={} store={} items={} total={}k method={}",
            user_id, cart.store_id, len(cart.items),
            cart.estimated_total, mandate.payment_method,
        )

        # 1. Spending limit check
        if cart.estimated_total > mandate.spending_limit:
            logger.warning(
                "payment:limit_exceeded | user_id={} total={}k limit={}k store={}",
                user_id, cart.estimated_total, mandate.spending_limit, cart.store_id,
            )
            raise ValueError(
                f"Tổng đơn hàng {cart.estimated_total:.0f}k VND vượt hạn mức "
                f"{mandate.spending_limit:.0f}k VND. Vui lòng điều chỉnh hạn mức trong Ví AI."
            )

        # 1b. Store preference check
        import json as _json
        preferred = _json.loads(mandate.preferred_store_ids or "[]")
        if preferred and cart.store_id not in preferred:
            logger.warning(
                "payment:store_not_allowed | user_id={} store={} allowed={}",
                user_id, cart.store_id, preferred,
            )
            raise ValueError(
                f"Cửa hàng '{cart.store_name}' không nằm trong danh sách được phép "
                f"trong Ví AI của bạn. Vui lòng cập nhật cài đặt Ví AI."
            )

        # 2. Mock payment gateway
        payment = await self._mock_stripe_charge(
            cart.estimated_total, mandate.payment_method
        )
        if not payment.success:
            raise RuntimeError(
                payment.error_message or "Giao dịch thất bại. Vui lòng thử lại."
            )

        # 3. Persist order
        order = AgentOrder(
            user_id=user_id,
            payment_mandate_id=mandate.id,
            store_id=cart.store_id,
            store_name=cart.store_name,
            status="paid",
            subtotal=cart.subtotal,
            delivery_fee=cart.delivery_fee,
            total=cart.estimated_total,
            payment_method=mandate.payment_method,
            chat_session_id=chat_session_id,
            transaction_id=payment.transaction_id,
            intent_description=cart.intent_description,
            created_at=datetime.utcnow(),
        )
        db.add(order)
        await db.flush()  # get order.id before adding items

        for item in cart.items:
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    product_emoji=item.product_emoji,
                    unit=item.unit,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                )
            )

        await db.commit()
        await db.refresh(order)

        logger.info(
            "payment:success | user_id={} order_id={} store={} total={}k txn={}",
            user_id,
            order.id,
            cart.store_id,
            cart.estimated_total,
            payment.transaction_id,
        )

        return OrderResult(
            order_id=order.id,
            status=order.status,
            total=cart.estimated_total,
            transaction_id=payment.transaction_id,
        )

    async def _mock_stripe_charge(
        self, amount: float, method: str
    ) -> PaymentResult:
        """
        Simulate payment gateway call.
        95% success rate, 0.3s simulated network latency.
        """
        await asyncio.sleep(0.3)
        if random.random() < 0.95:
            txn_id = f"mock_txn_{uuid.uuid4().hex[:8]}"
            logger.debug(
                "payment:mock_charge | method={} amount={}k txn={} status=approved",
                method, amount, txn_id,
            )
            return PaymentResult(success=True, transaction_id=txn_id)
        logger.warning(
            "payment:mock_declined | method={} amount={}k reason=random_5pct_failure",
            method, amount,
        )
        return PaymentResult(
            success=False,
            transaction_id="",
            error_message="Giao dịch bị từ chối (mock simulation). Vui lòng thử lại.",
        )


# ── Module singleton ───────────────────────────────────────────────────────────

payment_service = PaymentService()
