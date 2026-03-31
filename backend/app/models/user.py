"""User models."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    """User model."""

    __tablename__ = "users"

    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Relationships
    profile: Optional["Profile"] = Relationship(back_populates="user")
    recipes: List["Recipe"] = Relationship(back_populates="author")
    posts: List["Post"] = Relationship(back_populates="author")
    meal_plans: List["MealPlan"] = Relationship(back_populates="user")


class Profile(SQLModel, table=True):
    """User profile model."""

    __tablename__ = "profiles"

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, index=True)
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None  # in kg
    height: Optional[float] = None  # in cm
    gender: Optional[str] = None
    dietary_preference: Optional[str] = None  # vegetarian, vegan, etc.
    allergies: Optional[str] = None  # JSON string
    health_conditions: Optional[str] = None  # JSON string
    goal: Optional[str] = None  # weight_loss, muscle_gain, maintenance
    target_calories: Optional[int] = None
    preferences: Optional[str] = None  # JSON string for various preferences
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Relationships
    user: Optional[User] = Relationship(back_populates="profile")


class UserPersonaSetting(SQLModel, table=True):
    """Lưu persona đang active của mỗi user và các custom overrides."""

    __tablename__ = "user_persona_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, index=True, nullable=False)
    active_persona_id: str = Field(default="asian_chef", nullable=False)
    # JSON string — chỉ lưu các keys user muốn override (system/recipe_prefix/meal_plan_prefix)
    custom_prompt_overrides: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
