"""Social schemas."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


class PostCreate(BaseModel):
    """Post creation schema."""

    content: str = Field(..., min_length=1, max_length=5000)
    image_urls: Optional[List[str]] = None
    video_url: Optional[str] = None
    recipe_id: Optional[int] = None


class PostResponse(BaseModel):
    """Post response schema."""

    id: int
    author_id: str
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    content: str
    image_urls: Optional[List[str]] = None
    video_url: Optional[str] = None
    recipe_id: Optional[int] = None
    like_count: int = 0
    comment_count: int = 0
    is_liked_by_me: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    """Comment creation schema."""

    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[int] = None


class CommentResponse(BaseModel):
    """Comment response schema."""

    id: int
    user_id: str
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    content: str
    like_count: int = 0
    parent_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
