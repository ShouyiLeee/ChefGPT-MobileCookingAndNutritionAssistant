"""Recipe models."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Text, ARRAY, String


class Ingredient(SQLModel, table=True):
    """Ingredient model."""

    __tablename__ = "ingredients"

    id: int = Field(primary_key=True)
    name: str = Field(unique=True, index=True, nullable=False)
    name_vi: Optional[str] = Field(index=True)  # Vietnamese name
    category: Optional[str] = None  # vegetable, meat, spice, etc.
    unit: Optional[str] = None  # default unit
    calories_per_100g: Optional[float] = None
    protein_per_100g: Optional[float] = None
    carbs_per_100g: Optional[float] = None
    fat_per_100g: Optional[float] = None
    fiber_per_100g: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    recipe_ingredients: List["RecipeIngredient"] = Relationship(back_populates="ingredient")


class Recipe(SQLModel, table=True):
    """Recipe model."""

    __tablename__ = "recipes"

    id: int = Field(primary_key=True)
    author_id: Optional[str] = Field(foreign_key="users.id", index=True)
    title: str = Field(index=True, nullable=False)
    description: str = Field(sa_column=Column(Text))
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    prep_time: Optional[int] = None  # in minutes
    cook_time: Optional[int] = None  # in minutes
    total_time: Optional[int] = None  # in minutes
    servings: Optional[int] = Field(default=4)
    difficulty: Optional[str] = None  # easy, medium, hard
    cuisine: Optional[str] = None  # vietnamese, thai, etc.
    category: Optional[str] = None  # breakfast, lunch, dinner, snack
    tags: Optional[str] = None  # JSON array as string
    is_public: bool = Field(default=True)
    view_count: int = Field(default=0)
    like_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Embeddings for RAG
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(3072))  # OpenAI embedding dimension
    )

    # Relationships
    author: Optional["User"] = Relationship(back_populates="recipes")
    recipe_ingredients: List["RecipeIngredient"] = Relationship(back_populates="recipe")
    steps: List["RecipeStep"] = Relationship(back_populates="recipe")
    nutrition: Optional["RecipeNutrition"] = Relationship(back_populates="recipe")


class RecipeIngredient(SQLModel, table=True):
    """Recipe-Ingredient junction table with quantity."""

    __tablename__ = "recipe_ingredients"

    id: int = Field(primary_key=True)
    recipe_id: int = Field(foreign_key="recipes.id", index=True)
    ingredient_id: int = Field(foreign_key="ingredients.id", index=True)
    quantity: float = Field(nullable=False)
    unit: str = Field(nullable=False)
    notes: Optional[str] = None
    is_optional: bool = Field(default=False)

    # Relationships
    recipe: Optional[Recipe] = Relationship(back_populates="recipe_ingredients")
    ingredient: Optional[Ingredient] = Relationship(back_populates="recipe_ingredients")


class RecipeStep(SQLModel, table=True):
    """Recipe cooking steps."""

    __tablename__ = "recipe_steps"

    id: int = Field(primary_key=True)
    recipe_id: int = Field(foreign_key="recipes.id", index=True)
    step_number: int = Field(nullable=False)
    instruction: str = Field(sa_column=Column(Text), nullable=False)
    image_url: Optional[str] = None
    duration: Optional[int] = None  # duration in seconds
    timer_required: bool = Field(default=False)

    # Relationships
    recipe: Optional[Recipe] = Relationship(back_populates="steps")


class RecipeNutrition(SQLModel, table=True):
    """Nutrition information for recipes."""

    __tablename__ = "recipe_nutrition"

    id: int = Field(primary_key=True)
    recipe_id: int = Field(foreign_key="recipes.id", unique=True, index=True)
    calories: Optional[float] = None
    protein: Optional[float] = None  # in grams
    carbs: Optional[float] = None  # in grams
    fat: Optional[float] = None  # in grams
    fiber: Optional[float] = None  # in grams
    sugar: Optional[float] = None  # in grams
    sodium: Optional[float] = None  # in mg
    cholesterol: Optional[float] = None  # in mg
    serving_size: Optional[str] = None

    # Relationships
    recipe: Optional[Recipe] = Relationship(back_populates="nutrition")
