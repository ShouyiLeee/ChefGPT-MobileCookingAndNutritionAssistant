"""CustomPersona — user-created persona templates stored in DB."""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CustomPersona(SQLModel, table=True):
    """
    User-created persona — complementary to the built-in JSON-based system personas.

    System personas (JSON files): read-only, is_system=True (not stored here).
    Custom personas (this model): full CRUD by the owner.

    Visibility:
      is_public=True  → visible to all authenticated users in GET /personas
      is_public=False → visible only to the creator
    """

    __tablename__ = "custom_personas"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Slug used in API / persona_id field — e.g. "custom_abc12345"
    slug: str = Field(unique=True, index=True, nullable=False)

    # Owner
    created_by: str = Field(foreign_key="users.id", index=True, nullable=False)

    # Display
    name: str = Field(nullable=False)
    description: str = Field(default="")
    icon: str = Field(default="👨‍🍳")
    color: str = Field(default="#6B7280")  # hex color

    # LLM prompts
    system_prompt: str = Field(default="")
    recipe_prefix: str = Field(default="")
    meal_plan_prefix: str = Field(default="")

    # Filters & actions (stored as JSON arrays)
    cuisine_filters: Optional[str] = Field(default="[]")   # JSON string
    quick_actions: Optional[str] = Field(default="[]")     # JSON string

    # Sharing
    is_public: bool = Field(default=True)

    # Lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
