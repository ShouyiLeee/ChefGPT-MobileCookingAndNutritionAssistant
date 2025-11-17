"""Recipe schemas."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


class IngredientBase(BaseModel):
    """Base ingredient schema."""

    name: str
    quantity: float
    unit: str


class RecipeIngredientResponse(BaseModel):
    """Recipe ingredient response schema."""

    ingredient_id: int
    name: str
    quantity: float
    unit: str
    is_available: bool = False


class RecipeStepBase(BaseModel):
    """Recipe step base schema."""

    step_number: int
    instruction: str
    image_url: Optional[str] = None
    duration: Optional[int] = None


class RecipeStepResponse(RecipeStepBase):
    """Recipe step response schema."""

    id: int

    class Config:
        from_attributes = True


class NutritionInfoResponse(BaseModel):
    """Nutrition info response schema."""

    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None

    class Config:
        from_attributes = True


class RecipeCreate(BaseModel):
    """Recipe creation schema."""

    title: str = Field(..., min_length=3, max_length=200)
    description: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: int = 4
    difficulty: Optional[str] = None
    cuisine: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    ingredients: List[IngredientBase]
    steps: List[RecipeStepBase]


class RecipeUpdate(BaseModel):
    """Recipe update schema."""

    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    cuisine: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class RecipeResponse(BaseModel):
    """Recipe response schema."""

    id: int
    title: str
    description: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    total_time: Optional[int] = None
    servings: int
    difficulty: Optional[str] = None
    cuisine: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    ingredients: List[RecipeIngredientResponse] = []
    steps: List[RecipeStepResponse] = []
    nutrition: Optional[NutritionInfoResponse] = None
    author_id: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeListResponse(BaseModel):
    """Recipe list response schema."""

    id: int
    title: str
    description: str
    image_url: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    difficulty: Optional[str] = None
    servings: int
    cuisine: Optional[str] = None
    like_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
