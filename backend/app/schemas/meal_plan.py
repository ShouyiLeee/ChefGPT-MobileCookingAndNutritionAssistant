"""Meal plan schemas."""
from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import List, Optional


class MealPlanGenerateRequest(BaseModel):
    """Meal plan generation request schema."""

    start_date: date
    end_date: date
    goal: Optional[str] = None  # weight_loss, muscle_gain, maintenance
    target_calories: Optional[int] = Field(None, ge=1000, le=5000)
    dietary_preferences: Optional[List[str]] = None
    exclude_ingredients: Optional[List[str]] = None


class MealItemResponse(BaseModel):
    """Meal item response schema."""

    id: int
    recipe_id: int
    recipe_title: str
    meal_date: date
    meal_type: str
    servings: int
    is_completed: bool

    class Config:
        from_attributes = True


class MealPlanResponse(BaseModel):
    """Meal plan response schema."""

    id: int
    title: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    goal: Optional[str] = None
    target_calories: Optional[int] = None
    is_active: bool
    meal_items: List[MealItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
