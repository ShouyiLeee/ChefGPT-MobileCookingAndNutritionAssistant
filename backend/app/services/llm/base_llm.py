"""Abstract LLM interface — all providers must implement these 4 methods."""
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Common interface for Gemini, OpenAI, and Anthropic providers."""

    @abstractmethod
    async def suggest_recipes(
        self, ingredients: list[str], filters: list[str] | None = None
    ) -> dict:
        """Suggest dishes from available ingredients. Returns {dishes: [...]}."""
        ...

    @abstractmethod
    async def recognize_ingredients(self, image_bytes: bytes) -> dict:
        """Identify food ingredients from an image. Returns {ingredients: [...]}."""
        ...

    @abstractmethod
    async def generate_meal_plan(
        self, goal: str, days: int, calories_target: int
    ) -> dict:
        """Generate a multi-day meal plan. Returns {plan: [...], nutrition_summary: {...}}."""
        ...

    @abstractmethod
    async def chat(self, message: str, history: list[dict] | None = None) -> str:
        """Respond to a cooking/nutrition query. Returns plain text."""
        ...
