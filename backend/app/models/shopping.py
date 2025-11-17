"""Shopping list models."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class ShoppingList(SQLModel, table=True):
    """Shopping list model."""

    __tablename__ = "shopping_lists"

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    title: str = Field(nullable=False)
    meal_plan_id: Optional[int] = Field(foreign_key="meal_plans.id", default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Relationships
    user: Optional["User"] = Relationship(back_populates="shopping_lists")
    items: List["ShoppingItem"] = Relationship(back_populates="shopping_list")


class ShoppingItem(SQLModel, table=True):
    """Shopping list item model."""

    __tablename__ = "shopping_items"

    id: int = Field(primary_key=True)
    shopping_list_id: int = Field(foreign_key="shopping_lists.id", index=True)
    ingredient_id: Optional[int] = Field(foreign_key="ingredients.id", default=None)
    name: str = Field(nullable=False)
    quantity: float = Field(nullable=False)
    unit: str = Field(nullable=False)
    category: Optional[str] = None  # produce, meat, dairy, etc.
    is_purchased: bool = Field(default=False)
    purchased_at: Optional[datetime] = None
    notes: Optional[str] = None

    # Relationships
    shopping_list: Optional[ShoppingList] = Relationship(back_populates="items")
    ingredient: Optional["Ingredient"] = Relationship()
