"""
AP2 Agentic Payment API endpoints.

Routes:
  POST /payment-mandate            — Create/update user's spending mandate
  GET  /payment-mandate            — Get user's current mandate
  POST /orders/agent               — Place an agent order using a CartMandate
  GET  /orders                     — List user's orders (newest first)
  GET  /orders/{order_id}          — Get order detail with items
  POST /orders/{order_id}/cancel   — Cancel a pending/confirmed order
"""
import asyncio
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.database import async_session_maker, get_session
from app.core.security import get_current_user_id
from app.models.order import AgentOrder, OrderItem, PaymentMandate
from app.schemas.order import (
    AgentOrderResponse,
    CartMandateSchema,
    ConfirmPurchaseRequest,
    ConfirmPurchaseResponse,
    OrderItemResponse,
    PaymentMandateCreate,
    PaymentMandateResponse,
)
from app.services.payment_service import payment_service
from app.services.shopping_agent import CartMandate, CartMandateItem

router = APIRouter(tags=["AP2 Payments"])

_CANCELLABLE_STATUSES = {"pending_confirmation", "confirmed"}

# ── Delivery simulation ───────────────────────────────────────────────────────

async def _simulate_delivery(order_id: int, delay_delivering: float = 5.0, delay_delivered: float = 15.0) -> None:
    """
    Background task: simulate order lifecycle transitions.
    paid → delivering (after ~5s) → delivered (after ~15s more).
    In production replace with real webhook/push notification.
    """
    await asyncio.sleep(delay_delivering)
    async with async_session_maker() as db:
        try:
            order = await db.get(AgentOrder, order_id)
            if order and order.status == "paid":
                order.status = "delivering"
                order.updated_at = datetime.utcnow()
                await db.commit()
                logger.info("delivery:delivering | order_id={}", order_id)
        except Exception as e:
            logger.warning("delivery:error | order_id={} stage=delivering err={}", order_id, str(e)[:80])

    await asyncio.sleep(delay_delivered)
    async with async_session_maker() as db:
        try:
            order = await db.get(AgentOrder, order_id)
            if order and order.status == "delivering":
                order.status = "delivered"
                order.updated_at = datetime.utcnow()
                await db.commit()
                logger.info("delivery:delivered | order_id={}", order_id)
        except Exception as e:
            logger.warning("delivery:error | order_id={} stage=delivered err={}", order_id, str(e)[:80])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mandate_to_response(m: PaymentMandate) -> PaymentMandateResponse:
    return PaymentMandateResponse(
        id=m.id,
        payment_method=m.payment_method,
        spending_limit=m.spending_limit,
        preferred_store_ids=json.loads(m.preferred_store_ids or "[]"),
        auto_buy_enabled=m.auto_buy_enabled,
        is_active=m.is_active,
    )


def _schema_to_cart_mandate(schema: CartMandateSchema) -> CartMandate:
    items = [
        CartMandateItem(
            product_id=i.product_id,
            product_name=i.product_name,
            product_emoji=i.product_emoji,
            unit=i.unit,
            quantity=i.quantity,
            unit_price=i.unit_price,
            subtotal=i.subtotal,
        )
        for i in schema.items
    ]
    return CartMandate(
        store_id=schema.store_id,
        store_name=schema.store_name,
        items=items,
        subtotal=schema.subtotal,
        delivery_fee=schema.delivery_fee,
        estimated_total=schema.estimated_total,
        intent_description=schema.intent_description,
    )


async def _order_to_response(order: AgentOrder, db: AsyncSession) -> AgentOrderResponse:
    items_result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )
    items = [
        OrderItemResponse(
            product_id=i.product_id,
            product_name=i.product_name,
            product_emoji=i.product_emoji,
            quantity=i.quantity,
            unit=i.unit,
            unit_price=i.unit_price,
            subtotal=i.subtotal,
        )
        for i in items_result.scalars().all()
    ]
    return AgentOrderResponse(
        id=order.id,
        store_id=order.store_id,
        store_name=order.store_name,
        status=order.status,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        total=order.total,
        payment_method=order.payment_method,
        transaction_id=order.transaction_id,
        intent_description=order.intent_description,
        items=items,
        created_at=order.created_at,
    )


# ── Payment Mandate Endpoints ─────────────────────────────────────────────────

@router.post("/payment-mandate", response_model=PaymentMandateResponse)
async def upsert_payment_mandate(
    body: PaymentMandateCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> PaymentMandateResponse:
    """
    Create or update the user's AP2 Payment Mandate.
    Each user has exactly one mandate (upsert).
    """
    result = await session.execute(
        select(PaymentMandate).where(
            PaymentMandate.user_id == user_id,
            PaymentMandate.is_active == True,
        )
    )
    mandate = result.scalar_one_or_none()

    preferred_json = json.dumps(body.preferred_store_ids or [], ensure_ascii=False)

    if mandate:
        mandate.payment_method = body.payment_method
        mandate.spending_limit = body.spending_limit
        mandate.preferred_store_ids = preferred_json
        mandate.auto_buy_enabled = body.auto_buy_enabled
        mandate.updated_at = datetime.utcnow()
    else:
        mandate = PaymentMandate(
            user_id=user_id,
            payment_method=body.payment_method,
            spending_limit=body.spending_limit,
            preferred_store_ids=preferred_json,
            auto_buy_enabled=body.auto_buy_enabled,
            created_at=datetime.utcnow(),
        )
        session.add(mandate)

    await session.commit()
    await session.refresh(mandate)

    logger.info(
        "mandate:upsert | user_id={} method={} limit={}k",
        user_id, body.payment_method, body.spending_limit,
    )
    return _mandate_to_response(mandate)


@router.get("/payment-mandate", response_model=PaymentMandateResponse)
async def get_payment_mandate(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> PaymentMandateResponse:
    """Get the user's current Payment Mandate settings."""
    result = await session.execute(
        select(PaymentMandate).where(
            PaymentMandate.user_id == user_id,
            PaymentMandate.is_active == True,
        )
    )
    mandate = result.scalar_one_or_none()
    if not mandate:
        logger.debug("mandate:not_found | user_id={}", user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chưa thiết lập Ví AI. Vui lòng cấu hình trong phần Ví AI & Hạn mức.",
        )
    logger.debug(
        "mandate:get | user_id={} method={} limit={}k",
        user_id, mandate.payment_method, mandate.spending_limit,
    )
    return _mandate_to_response(mandate)


# ── Agent Order Endpoints ─────────────────────────────────────────────────────

@router.post(
    "/orders/agent",
    response_model=ConfirmPurchaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def place_agent_order(
    body: ConfirmPurchaseRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ConfirmPurchaseResponse:
    """
    Place an agent order using a CartMandate.
    Used by both the chat confirm flow and the grocery screen checkout.
    """
    logger.info(
        "order:place_start | user_id={} store={} items={} total={}k",
        user_id, body.cart_mandate.store_id,
        len(body.cart_mandate.items), body.cart_mandate.estimated_total,
    )
    # Load mandate
    if body.payment_mandate_id:
        mandate = await session.get(PaymentMandate, body.payment_mandate_id)
        if not mandate or mandate.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mandate not found",
            )
    else:
        result = await session.execute(
            select(PaymentMandate).where(
                PaymentMandate.user_id == user_id,
                PaymentMandate.is_active == True,
            )
        )
        mandate = result.scalar_one_or_none()

    if not mandate:
        logger.warning("order:mandate_missing | user_id={}", user_id)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Chưa thiết lập Ví AI. Vui lòng cấu hình hạn mức thanh toán trong phần Ví AI.",
        )

    cart = _schema_to_cart_mandate(body.cart_mandate)

    try:
        result_obj = await payment_service.execute_payment(
            user_id=user_id,
            cart=cart,
            mandate=mandate,
            db=session,
        )
    except ValueError as e:
        logger.warning(
            "order:spending_limit_exceeded | user_id={} total={}k limit={}k",
            user_id, cart.estimated_total, mandate.spending_limit,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(
            "order:payment_failed | user_id={} store={} total={}k error={}",
            user_id, cart.store_id, cart.estimated_total, str(e)[:120],
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    # Start delivery simulation in background
    background_tasks.add_task(_simulate_delivery, result_obj.order_id)

    return ConfirmPurchaseResponse(
        order_id=result_obj.order_id,
        status=result_obj.status,
        total=cart.estimated_total,
        store_name=cart.store_name,
        estimated_delivery="30–60 phút",
        transaction_id=result_obj.transaction_id,
    )


@router.get("/orders", response_model=List[AgentOrderResponse])
async def list_orders(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> List[AgentOrderResponse]:
    """List the user's agent orders, newest first."""
    offset = (page - 1) * limit
    result = await session.execute(
        select(AgentOrder)
        .where(AgentOrder.user_id == user_id)
        .order_by(AgentOrder.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    orders = result.scalars().all()
    logger.debug(
        "order:list | user_id={} count={} page={}",
        user_id, len(orders), page,
    )
    return [await _order_to_response(o, session) for o in orders]


@router.get("/orders/{order_id}", response_model=AgentOrderResponse)
async def get_order(
    order_id: int,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> AgentOrderResponse:
    """Get a specific order by ID (ownership verified)."""
    order = await session.get(AgentOrder, order_id)
    if not order or order.user_id != user_id:
        logger.debug("order:not_found | user_id={} order_id={}", user_id, order_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    logger.debug(
        "order:get | user_id={} order_id={} status={}",
        user_id, order_id, order.status,
    )
    return await _order_to_response(order, session)


@router.post("/orders/{order_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_order(
    order_id: int,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Cancel a pending or confirmed order."""
    order = await session.get(AgentOrder, order_id)
    if not order or order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if order.status not in _CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Không thể huỷ đơn có trạng thái '{order.status}'. "
                   f"Chỉ có thể huỷ đơn ở trạng thái: {', '.join(_CANCELLABLE_STATUSES)}.",
        )
    order.status = "cancelled"
    order.updated_at = datetime.utcnow()
    await session.commit()

    logger.info("order:cancelled | user_id={} order_id={}", user_id, order_id)
    return {"success": True, "order_id": order_id, "status": "cancelled"}


@router.get("/orders/stats")
async def get_order_stats(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return aggregate spending stats for the current user."""
    count_result = await session.execute(
        select(func.count(AgentOrder.id)).where(AgentOrder.user_id == user_id)
    )
    total_orders = count_result.scalar_one() or 0

    sum_result = await session.execute(
        select(func.sum(AgentOrder.total)).where(
            AgentOrder.user_id == user_id,
            AgentOrder.status.in_(["paid", "delivering", "delivered"]),
        )
    )
    total_spent = sum_result.scalar_one() or 0.0

    delivered_result = await session.execute(
        select(func.count(AgentOrder.id)).where(
            AgentOrder.user_id == user_id,
            AgentOrder.status == "delivered",
        )
    )
    delivered_count = delivered_result.scalar_one() or 0

    logger.debug(
        "order:stats | user_id={} total_orders={} total_spent={}k delivered={}",
        user_id, total_orders, total_spent, delivered_count,
    )
    return {
        "total_orders": total_orders,
        "total_spent": round(total_spent, 1),
        "delivered_count": delivered_count,
    }
