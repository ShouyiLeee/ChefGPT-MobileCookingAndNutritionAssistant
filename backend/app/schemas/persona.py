"""Pydantic schemas cho Persona API."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class PersonaListItem(BaseModel):
    """Metadata của 1 persona — không bao gồm prompts (server-side only)."""

    id: str
    name: str
    description: str
    icon: str
    color: str
    is_default: bool = False
    is_system: bool = True          # True = built-in JSON, False = user-created
    created_by: Optional[str] = None  # user_id, None for system personas
    is_public: bool = True
    cuisine_filters: list[str] = []
    quick_actions: list[str] = []


class PersonaPromptsDetail(BaseModel):
    """Full prompt detail — only returned for personas the user owns."""

    system: str = ""
    recipe_prefix: str = ""
    meal_plan_prefix: str = ""


class PersonaDetailResponse(PersonaListItem):
    """Full persona detail including prompts (own custom personas only)."""

    prompts: Optional[PersonaPromptsDetail] = None


class CreatePersonaRequest(BaseModel):
    """Request body cho POST /personas — tạo custom persona mới."""

    name: str = Field(..., min_length=2, max_length=50)
    description: str = Field(default="", max_length=200)
    icon: str = Field(default="👨‍🍳", max_length=10)
    color: str = Field(default="#6B7280", pattern=r"^#[0-9A-Fa-f]{6}$")
    system_prompt: str = Field(
        default="",
        max_length=2000,
        description="System prompt inject vào mỗi chat. Để trống = dùng default.",
    )
    recipe_prefix: str = Field(default="", max_length=1000)
    meal_plan_prefix: str = Field(default="", max_length=1000)
    cuisine_filters: list[str] = Field(default=[])
    quick_actions: list[str] = Field(default=[])
    is_public: bool = Field(default=True)


class UpdatePersonaRequest(BaseModel):
    """Request body cho PUT /personas/{id} — chỉnh sửa custom persona."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    description: Optional[str] = Field(default=None, max_length=200)
    icon: Optional[str] = Field(default=None, max_length=10)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    system_prompt: Optional[str] = Field(default=None, max_length=2000)
    recipe_prefix: Optional[str] = Field(default=None, max_length=1000)
    meal_plan_prefix: Optional[str] = Field(default=None, max_length=1000)
    cuisine_filters: Optional[list[str]] = None
    quick_actions: Optional[list[str]] = None
    is_public: Optional[bool] = None


class UserPersonaSettingResponse(BaseModel):
    """Response cho GET /personas/me."""

    active_persona_id: str
    persona: PersonaListItem
    has_custom_overrides: bool


class SetPersonaRequest(BaseModel):
    """Request body cho PUT /personas/me."""

    persona_id: str = Field(..., description="ID của persona muốn đặt làm active")
    custom_overrides: Optional[dict[str, Any]] = Field(
        default=None,
        description="Override một phần prompt. Allowed keys: system, recipe_prefix, meal_plan_prefix",
    )
