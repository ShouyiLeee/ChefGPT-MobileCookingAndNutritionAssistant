"""Social media models."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text


class Post(SQLModel, table=True):
    """Social media post model."""

    __tablename__ = "posts"

    id: int = Field(primary_key=True)
    author_id: str = Field(foreign_key="users.id", index=True)
    content: str = Field(sa_column=Column(Text), nullable=False)
    image_urls: Optional[str] = None  # JSON array as string
    video_url: Optional[str] = None
    recipe_id: Optional[int] = Field(foreign_key="recipes.id", index=True)
    like_count: int = Field(default=0)
    comment_count: int = Field(default=0)
    share_count: int = Field(default=0)
    is_public: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Relationships
    author: Optional["User"] = Relationship(back_populates="posts")
    comments: List["Comment"] = Relationship(back_populates="post")
    likes: List["Like"] = Relationship(back_populates="post")


class Comment(SQLModel, table=True):
    """Comment model."""

    __tablename__ = "comments"

    id: int = Field(primary_key=True)
    post_id: int = Field(foreign_key="posts.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    parent_id: Optional[int] = Field(foreign_key="comments.id", default=None)
    content: str = Field(sa_column=Column(Text), nullable=False)
    like_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Relationships
    post: Optional[Post] = Relationship(back_populates="comments")
    replies: List["Comment"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"remote_side": "Comment.id"}
    )
    parent: Optional["Comment"] = Relationship(back_populates="replies")


class Like(SQLModel, table=True):
    """Like model."""

    __tablename__ = "likes"

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    post_id: Optional[int] = Field(foreign_key="posts.id", index=True, default=None)
    comment_id: Optional[int] = Field(foreign_key="comments.id", index=True, default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    post: Optional[Post] = Relationship(back_populates="likes")


class Bookmark(SQLModel, table=True):
    """Bookmark model for saving recipes and posts."""

    __tablename__ = "bookmarks"

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    recipe_id: Optional[int] = Field(foreign_key="recipes.id", index=True, default=None)
    post_id: Optional[int] = Field(foreign_key="posts.id", index=True, default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
