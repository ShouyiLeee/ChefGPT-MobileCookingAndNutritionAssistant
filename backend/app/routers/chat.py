"""Chat router — cooking & nutrition assistant powered by Gemini."""
import asyncio
import time
from dataclasses import replace as dc_replace
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import async_session_maker, get_session
from app.core.security import get_current_user_id
from app.models.chat import ChatMessage, ChatSession
from app.models.order import PaymentMandate
from app.schemas.order import (
    CartMandateSchema,
    CartMandateItemSchema,
    ConfirmPurchaseRequest,
    ConfirmPurchaseResponse,
    ShoppingSuggestionSchema,
)
from app.services.cache import cache_service
from app.services.llm import llm_provider
from app.services.memory_service import memory_service
from app.services.payment_service import payment_service
from app.services.persona_context import PersonaContextResolver
from app.services.shopping_agent import shopping_agent_service

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatQueryRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    persona_id: Optional[str] = None  # override active persona for this request


class ChatMessageResponse(BaseModel):
    id: str
    message: str
    role: str
    timestamp: datetime
    shopping_suggestion: Optional[dict] = None  # ShoppingSuggestionSchema serialized


class ChatHistoryResponse(BaseModel):
    session_id: int
    messages: List[ChatMessageResponse]
    created_at: datetime


async def _extract_memory_bg(user_id: str, user_message: str) -> None:
    """Background task: extract memory facts after chat response is sent."""
    async with async_session_maker() as db:
        try:
            await memory_service.extract_and_save(
                user_id, user_message, llm_provider, db, cache_service
            )
        except Exception as e:
            logger.warning(
                "bg:extract_memory | user_id={} error={}", user_id, str(e)[:100]
            )


@router.post("/query", response_model=ChatMessageResponse)
async def send_message(
    request: ChatQueryRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ChatMessageResponse:
    """Send a message to ChefGPT AI assistant."""
    t0 = time.perf_counter()
    logger.info(
        "router:chat | session_id={} message_len={}",
        request.session_id, len(request.message),
    )

    # Get or create chat session
    if request.session_id:
        result = await session.execute(
            select(ChatSession).where(
                ChatSession.id == request.session_id,
                ChatSession.user_id == user_id,
            )
        )
        chat_session = result.scalar_one_or_none()
        if not chat_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
        logger.debug("db:chat | existing session_id={}", chat_session.id)
    else:
        chat_session = ChatSession(user_id=user_id, title="New Chat")
        session.add(chat_session)
        await session.flush()
        logger.debug("db:chat | new session_id={}", chat_session.id)

    # Load recent history for context (last 10 messages)
    history_result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    recent = list(reversed(history_result.scalars().all()))
    history = [{"role": msg.role, "parts": [msg.content]} for msg in recent]
    logger.debug("db:chat | history_loaded turns={}", len(recent))

    # Save user message
    user_msg = ChatMessage(session_id=chat_session.id, role="user", content=request.message)
    session.add(user_msg)
    await session.commit()

    # Resolve persona
    resolver = PersonaContextResolver(session, cache_service)
    persona = await resolver.resolve(user_id, request.persona_id)

    # Inject user memory into system prompt
    memory_block = await memory_service.get_context_block(user_id, session, cache_service)
    if memory_block:
        persona = dc_replace(
            persona,
            system_prompt=persona.system_prompt + "\n\n" + memory_block,
        )

    # Schedule memory extraction as background task (non-blocking)
    background_tasks.add_task(_extract_memory_bg, user_id, request.message)

    # Call LLM
    t_llm = time.perf_counter()
    try:
        reply = await llm_provider.chat(request.message, history, persona=persona)
    except Exception as e:
        llm_ms = round((time.perf_counter() - t_llm) * 1000, 1)
        logger.error(
            "router:chat | llm_error={} llm_latency={}ms",
            str(e)[:200], llm_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )

    llm_ms = round((time.perf_counter() - t_llm) * 1000, 1)
    logger.debug(
        "router:chat | llm_ok reply_len={} llm_latency={}ms",
        len(reply), llm_ms,
    )

    # Save assistant message
    assistant_msg = ChatMessage(session_id=chat_session.id, role="model", content=reply)
    session.add(assistant_msg)
    await session.commit()
    await session.refresh(assistant_msg)

    # ── AP2: Detect shopping intent (3s hard cap — never slow down chat) ────────
    shopping_suggestion: Optional[dict] = None
    try:
        intent = await asyncio.wait_for(
            shopping_agent_service.detect_shopping_intent(request.message),
            timeout=3.0,
        )
        if intent and intent.has_intent:
            cart = await shopping_agent_service.build_cart_from_intent(intent)
            # Check if user has an active mandate
            mandate_result = await session.execute(
                select(PaymentMandate).where(
                    PaymentMandate.user_id == user_id,
                    PaymentMandate.is_active == True,
                )
            )
            mandate = mandate_result.scalar_one_or_none()
            suggestion = ShoppingSuggestionSchema(
                cart_mandate=CartMandateSchema(
                    store_id=cart.store_id,
                    store_name=cart.store_name,
                    items=[
                        CartMandateItemSchema(
                            product_id=i.product_id,
                            product_name=i.product_name,
                            product_emoji=i.product_emoji,
                            unit=i.unit,
                            quantity=i.quantity,
                            unit_price=i.unit_price,
                            subtotal=i.subtotal,
                        )
                        for i in cart.items
                    ],
                    subtotal=cart.subtotal,
                    delivery_fee=cart.delivery_fee,
                    estimated_total=cart.estimated_total,
                    intent_description=cart.intent_description,
                ),
                estimated_total=cart.estimated_total,
                requires_confirmation=True,
                mandate_id=mandate.id if mandate else None,
            )
            shopping_suggestion = suggestion.model_dump()
            logger.info(
                "router:chat | shopping_intent=true store={} items={} total={}k mandate_id={}",
                cart.store_id, len(cart.items), cart.estimated_total,
                mandate.id if mandate else None,
            )
        else:
            logger.debug("router:chat | shopping_intent=false")
    except asyncio.TimeoutError:
        logger.warning("router:chat | shopping_intent=timeout — skipping suggestion")
    except Exception as _e:
        logger.warning("router:chat | shopping_intent=error reason={}", str(_e)[:100])

    total_ms = round((time.perf_counter() - t0) * 1000, 1)
    logger.info(
        "router:chat | ok session_id={} reply_len={} history_turns={} llm_latency={}ms total_latency={}ms",
        chat_session.id, len(reply), len(recent), llm_ms, total_ms,
    )

    return ChatMessageResponse(
        id=str(assistant_msg.id),
        message=assistant_msg.content,
        role="assistant",
        timestamp=assistant_msg.created_at,
        shopping_suggestion=shopping_suggestion,
    )


@router.post("/confirm-purchase", response_model=ConfirmPurchaseResponse)
async def confirm_purchase(
    body: ConfirmPurchaseRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ConfirmPurchaseResponse:
    """
    Confirm and execute an agent purchase suggested during chat.
    Uses the user's active Payment Mandate (or the specified mandate_id).
    """
    logger.info(
        "chat:confirm_purchase | user_id={} store={} items={} total={}k",
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
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Chưa thiết lập Ví AI. Vui lòng cấu hình hạn mức thanh toán trong Profile → Ví AI.",
        )

    from app.services.shopping_agent import CartMandate, CartMandateItem
    cart = CartMandate(
        store_id=body.cart_mandate.store_id,
        store_name=body.cart_mandate.store_name,
        items=[
            CartMandateItem(
                product_id=i.product_id,
                product_name=i.product_name,
                product_emoji=i.product_emoji,
                unit=i.unit,
                quantity=i.quantity,
                unit_price=i.unit_price,
                subtotal=i.subtotal,
            )
            for i in body.cart_mandate.items
        ],
        subtotal=body.cart_mandate.subtotal,
        delivery_fee=body.cart_mandate.delivery_fee,
        estimated_total=body.cart_mandate.estimated_total,
        intent_description=body.cart_mandate.intent_description,
    )

    try:
        result_obj = await payment_service.execute_payment(
            user_id=user_id,
            cart=cart,
            mandate=mandate,
            db=session,
        )
    except ValueError as e:
        logger.warning(
            "chat:confirm_purchase | spending_limit_exceeded user_id={} total={}k limit={}k",
            user_id, cart.estimated_total, mandate.spending_limit,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error(
            "chat:confirm_purchase | payment_failed user_id={} store={} error={}",
            user_id, cart.store_id, str(e)[:120],
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    logger.info(
        "chat:confirm_purchase | ok user_id={} order_id={} total={}k txn={}",
        user_id, result_obj.order_id, cart.estimated_total, result_obj.transaction_id,
    )
    return ConfirmPurchaseResponse(
        order_id=result_obj.order_id,
        status=result_obj.status,
        total=cart.estimated_total,
        store_name=cart.store_name,
        estimated_delivery="30–60 phút",
        transaction_id=result_obj.transaction_id,
    )


@router.get("/history", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> List[ChatHistoryResponse]:
    """Get all chat sessions for the current user."""
    logger.debug("db:chat_history | fetching sessions")
    t0 = time.perf_counter()
    sessions_result = await session.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id, ChatSession.is_active == True)
        .order_by(ChatSession.created_at.desc())
    )
    sessions = sessions_result.scalars().all()

    history = []
    total_messages = 0
    for cs in sessions:
        msgs_result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == cs.id)
            .order_by(ChatMessage.created_at)
        )
        messages = [
            ChatMessageResponse(
                id=str(m.id), message=m.content, role=m.role, timestamp=m.created_at
            )
            for m in msgs_result.scalars().all()
        ]
        total_messages += len(messages)
        history.append(ChatHistoryResponse(
            session_id=cs.id, messages=messages, created_at=cs.created_at
        ))

    logger.info(
        "db:chat_history | sessions={} total_messages={} latency={}ms",
        len(sessions), total_messages, round((time.perf_counter() - t0) * 1000, 1),
    )
    return history
