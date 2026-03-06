"""Chat router — cooking & nutrition assistant powered by Gemini."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.chat import ChatSession, ChatMessage
from app.services.gemini import gemini_service

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
    else:
        chat_session = ChatSession(user_id=user_id, title="New Chat")
        session.add(chat_session)
        await session.flush()

    # Load recent history for context (last 10 messages)
    history_result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    recent = list(reversed(history_result.scalars().all()))
    history = [{"role": msg.role, "parts": [msg.content]} for msg in recent]

    # Save user message
    user_msg = ChatMessage(session_id=chat_session.id, role="user", content=request.message)
    session.add(user_msg)
    await session.commit()

    # Call Gemini
    try:
        reply = await gemini_service.chat(request.message, history)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )

    # Save assistant message
    assistant_msg = ChatMessage(session_id=chat_session.id, role="model", content=reply)
    session.add(assistant_msg)
    await session.commit()
    await session.refresh(assistant_msg)

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
    sessions_result = await session.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id, ChatSession.is_active == True)
        .order_by(ChatSession.created_at.desc())
    )
    sessions = sessions_result.scalars().all()

    history = []
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
        history.append(ChatHistoryResponse(
            session_id=cs.id, messages=messages, created_at=cs.created_at
        ))
    return history
