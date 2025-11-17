"""Meal plan models."""
from datetime import datetime, date
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text


class MealPlan(SQLModel, table=True):
    """Meal plan model."""

    __tablename__ = "meal_plans"

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    title: str = Field(nullable=False)
    description: Optional[str] = Field(sa_column=Column(Text))
    start_date: date = Field(nullable=False)
    end_date: date = Field(nullable=False)
    goal: Optional[str] = None  # weight_loss, muscle_gain, maintenance
    target_calories: Optional[int] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Relationships
    user: Optional["User"] = Relationship(back_populates="meal_plans")
    meal_items: List["MealItem"] = Relationship(back_populates="meal_plan")


class MealItem(SQLModel, table=True):
    """Individual meal in a meal plan."""

    __tablename__ = "meal_items"

    id: int = Field(primary_key=True)
    meal_plan_id: int = Field(foreign_key="meal_plans.id", index=True)
    recipe_id: int = Field(foreign_key="recipes.id", index=True)
    meal_date: date = Field(nullable=False, index=True)
    meal_type: str = Field(nullable=False)  # breakfast, lunch, dinner, snack
    servings: int = Field(default=1)
    notes: Optional[str] = None
    is_completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None

    # Relationships
    meal_plan: Optional[MealPlan] = Relationship(back_populates="meal_items")
    recipe: Optional["Recipe"] = Relationship()
