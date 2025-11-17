"""Vision API schemas."""
from pydantic import BaseModel
from typing import List, Optional


class IngredientRecognitionResponse(BaseModel):
    """Ingredient recognition response schema."""

    ingredients: List[str]
    confidence: float
    metadata: Optional[dict] = None


class IngredientDetail(BaseModel):
    """Detailed ingredient information."""

    name: str
    category: Optional[str] = None
    confidence: float
    quantity_estimate: Optional[str] = None
    freshness: Optional[str] = None  # fresh, aged, etc.
