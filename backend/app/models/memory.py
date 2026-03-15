"""UserMemory — persistent, per-user memory entries extracted from conversations."""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UserMemory(SQLModel, table=True):
    """
    Stores factual information about a user's food preferences, restrictions,
    goals, and context — extracted automatically from chat conversations.

    Uniqueness: (user_id, category, key, value) — prevents duplicate entries
    while allowing multiple values per key (e.g., two different allergies).
    """

    __tablename__ = "user_memories"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Owner
    user_id: str = Field(
        foreign_key="users.id",
        index=True,
        nullable=False,
    )

    # Classification
    category: str = Field(
        nullable=False,
        description=(
            "dietary | preference | aversion | goal | constraint | context"
        ),
    )
    key: str = Field(
        nullable=False,
        description=(
            "allergy | diet_type | favorite_cuisine | disliked_ingredient | "
            "nutrition_goal | cooking_time | household_size | cooking_skill | "
            "budget | equipment | other"
        ),
    )
    value: str = Field(nullable=False)

    # Metadata
    confidence: float = Field(default=1.0, description="0–1, higher = more certain")
    source: str = Field(
        default="inferred",
        description="explicit (user stated directly) | inferred (LLM extracted)",
    )

    # Lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
