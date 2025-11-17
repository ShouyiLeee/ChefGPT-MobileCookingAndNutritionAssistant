"""Chat schemas."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ChatQueryRequest(BaseModel):
    """Chat query request schema."""

    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[int] = None
    image_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""

    id: str
    message: str
    type: str  # user, assistant, system
    timestamp: datetime
    content: Optional[Dict[str, Any]] = None  # recipe_ids, ingredients, etc.
    is_loading: bool = False

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response schema."""

    session_id: int
    messages: List[ChatMessageResponse]
    created_at: datetime
