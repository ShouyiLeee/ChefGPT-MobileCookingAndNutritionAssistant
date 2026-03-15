"""Abstract LLM interface — all providers must implement these 4 methods."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.services.persona_context import PersonaContext


class BaseLLM(ABC):
    """Common interface for Gemini, OpenAI, and Anthropic providers."""

    @abstractmethod
    async def suggest_recipes(
        self,
        ingredients: list[str],
        filters: list[str] | None = None,
        persona: Optional["PersonaContext"] = None,
    ) -> dict:
        """Suggest dishes from available ingredients. Returns {dishes: [...]}."""
        ...

    @abstractmethod
    async def recognize_ingredients(self, image_bytes: bytes) -> dict:
        """Identify food ingredients from an image. Returns {ingredients: [...]}."""
        ...

    @abstractmethod
    async def generate_meal_plan(
        self,
        goal: str,
        days: int,
        calories_target: int,
        persona: Optional["PersonaContext"] = None,
        user_note: Optional[str] = None,
    ) -> dict:
        """Generate a multi-day meal plan. Returns {plan: [...], nutrition_summary: {...}}."""
        ...

    @abstractmethod
    async def chat(
        self,
        message: str,
        history: list[dict] | None = None,
        persona: Optional["PersonaContext"] = None,
    ) -> str:
        """Respond to a cooking/nutrition query. Returns plain text."""
        ...

    @abstractmethod
    async def extract_memory_facts(self, user_message: str) -> list[dict]:
        """
        Extract factual memory items from a single user message.
        Returns a list of dicts: [{category, key, value}, ...].
        Returns [] if no relevant facts found.
        Fast call — must use thinking_budget=0 / equivalent.
        """
        ...
