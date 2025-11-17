"""Chat router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.chat import (
    ChatQueryRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
)
from app.models.chat import ChatSession, ChatMessage
from sqlmodel import select
from datetime import datetime
import uuid

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/query", response_model=ChatMessageResponse)
async def send_message(
    request: ChatQueryRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ChatMessageResponse:
    """Send a message to the AI chatbot."""
    # Get or create session
    if request.session_id:
        statement = select(ChatSession).where(
            ChatSession.id == request.session_id,
            ChatSession.user_id == user_id,
        )
        result = await session.execute(statement)
        chat_session = result.scalar_one_or_none()

        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
    else:
        # Create new session
        chat_session = ChatSession(user_id=user_id, title="New Chat")
        session.add(chat_session)
        await session.flush()

    # Save user message
    user_message = ChatMessage(
        session_id=chat_session.id,
        role="user",
        content=request.message,
    )
    session.add(user_message)
    await session.commit()

    # TODO: Call LLM service to generate response
    # For now, return a placeholder response
    response_content = "This is a placeholder response. LLM integration coming soon!"

    # Save assistant message
    assistant_message = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content=response_content,
    )
    session.add(assistant_message)
    await session.commit()
    await session.refresh(assistant_message)

    return ChatMessageResponse(
        id=str(assistant_message.id),
        message=assistant_message.content,
        type="assistant",
        timestamp=assistant_message.created_at,
    )


@router.get("/history", response_model=list[ChatHistoryResponse])
async def get_chat_history(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> list[ChatHistoryResponse]:
    """Get user's chat history."""
    statement = select(ChatSession).where(
        ChatSession.user_id == user_id,
        ChatSession.is_active == True,
    ).order_by(ChatSession.created_at.desc())

    result = await session.execute(statement)
    sessions = result.scalars().all()

    history = []
    for chat_session in sessions:
        # Get messages for this session
        messages_statement = select(ChatMessage).where(
            ChatMessage.session_id == chat_session.id
        ).order_by(ChatMessage.created_at)

        messages_result = await session.execute(messages_statement)
        messages = messages_result.scalars().all()

        message_responses = [
            ChatMessageResponse(
                id=str(msg.id),
                message=msg.content,
                type=msg.role,
                timestamp=msg.created_at,
            )
            for msg in messages
        ]

        history.append(
            ChatHistoryResponse(
                session_id=chat_session.id,
                messages=message_responses,
                created_at=chat_session.created_at,
            )
        )

    return history
