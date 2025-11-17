"""Chat and conversation models."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text


class ChatSession(SQLModel, table=True):
    """Chat session model."""

    __tablename__ = "chat_sessions"

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    title: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Relationships
    messages: List["ChatMessage"] = Relationship(back_populates="session")


class ChatMessage(SQLModel, table=True):
    """Chat message model."""

    __tablename__ = "chat_messages"

    id: int = Field(primary_key=True)
    session_id: int = Field(foreign_key="chat_sessions.id", index=True)
    role: str = Field(nullable=False)  # user, assistant, system
    content: str = Field(sa_column=Column(Text), nullable=False)
    metadata: Optional[str] = None  # JSON string for additional data
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    session: Optional[ChatSession] = Relationship(back_populates="messages")
