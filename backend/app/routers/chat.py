"""Chat router — cooking & nutrition assistant powered by Gemini."""
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.chat import ChatMessage, ChatSession
from app.services.llm import llm_provider

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatQueryRequest(BaseModel):
    message: str
    session_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    id: str
    message: str
    role: str
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    session_id: int
    messages: List[ChatMessageResponse]
    created_at: datetime


@router.post("/query", response_model=ChatMessageResponse)
async def send_message(
    request: ChatQueryRequest,
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

    # Call LLM
    t_llm = time.perf_counter()
    try:
        reply = await llm_provider.chat(request.message, history)
    except Exception as e:
        logger.error(
            "router:chat | llm_error={} latency={}ms",
            str(e)[:200], round((time.perf_counter() - t_llm) * 1000, 1),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )

    # Save assistant message
    assistant_msg = ChatMessage(session_id=chat_session.id, role="model", content=reply)
    session.add(assistant_msg)
    await session.commit()
    await session.refresh(assistant_msg)

    total_ms = round((time.perf_counter() - t0) * 1000, 1)
    logger.info(
        "router:chat | ok session_id={} reply_len={} history_turns={} total_latency={}ms",
        chat_session.id, len(reply), len(recent), total_ms,
    )

    return ChatMessageResponse(
        id=str(assistant_msg.id),
        message=assistant_msg.content,
        role="assistant",
        timestamp=assistant_msg.created_at,
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
