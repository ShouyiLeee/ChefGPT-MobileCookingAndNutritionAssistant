"""Pydantic schemas for the memory API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.services.memory_service import VALID_CATEGORIES, VALID_KEYS


class MemoryResponse(BaseModel):
    id: int
    category: str
    key: str
    value: str
    confidence: float
    source: str
    created_at: datetime


class MemoryListResponse(BaseModel):
    memories: list[MemoryResponse]
    total: int
    # Pre-formatted context block (same as what gets injected into LLM)
    context_preview: str


class AddMemoryRequest(BaseModel):
    category: str = Field(
        description="dietary | preference | aversion | goal | constraint | context"
    )
    key: str = Field(
        description=(
            "allergy | diet_type | favorite_cuisine | disliked_ingredient | "
            "nutrition_goal | cooking_time | household_size | cooking_skill | "
            "budget | equipment | other"
        )
    )
    value: str = Field(max_length=200)


class UpdateMemoryRequest(BaseModel):
    value: str = Field(max_length=200, description="New value for the memory entry")


class DeleteAllResponse(BaseModel):
    deleted: int
    message: str
