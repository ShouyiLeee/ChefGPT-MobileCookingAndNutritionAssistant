"""Anthropic Claude provider (optional — set LLM_PROVIDER=anthropic)."""
from __future__ import annotations

import json
import re
from typing import Optional

from loguru import logger

from app.services.llm.base_llm import BaseLLM

_DEFAULT_SYSTEM = (
    "Bạn là ChefGPT — trợ lý nấu ăn và dinh dưỡng AI người Việt. "
    "Trả lời ngắn gọn, thực tế, bằng tiếng Việt."
)
_DEFAULT_RECIPE_SYSTEM = "Bạn là đầu bếp chuyên nghiệp người Việt. Chỉ trả về JSON, không có text ngoài JSON."
_DEFAULT_MEAL_PLAN_SYSTEM = "Bạn là chuyên gia dinh dưỡng người Việt. Chỉ trả về JSON."


class AnthropicLLM(BaseLLM):
    """Claude provider. Requires `anthropic` package and ANTHROPIC_API_KEY."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed — run: pip install anthropic>=0.30.0")
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def _message(self, system: str, user: str) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    @staticmethod
    def _parse_json(text: str) -> dict | list:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
        return json.loads(cleaned)

    async def suggest_recipes(
        self,
        ingredients: list[str],
        filters: list[str] | None = None,
        persona=None,
    ) -> dict:
        filters_str = ", ".join(filters) if filters else "không có"
        system = (
            f"{persona.recipe_prefix} Chỉ trả về JSON, không có text ngoài JSON."
            if persona and persona.recipe_prefix else _DEFAULT_RECIPE_SYSTEM
        )
        user = f"""Nguyên liệu: {", ".join(ingredients)}
Yêu cầu: {filters_str}

Gợi ý 3 món, trả về JSON:
{{"dishes": [{{"name": "...", "description": "...", "steps": ["..."], "time_minutes": 30, "difficulty": "easy", "nutrition": {{"calories": 350, "protein": 25, "carbs": 40, "fat": 10}}}}]}}"""
        text = await self._message(system, user)
        logger.debug("anthropic suggest_recipes done model={}", self._model)
        return self._parse_json(text)

    async def recognize_ingredients(self, image_bytes: bytes) -> dict:
        import base64

        b64 = base64.b64encode(image_bytes).decode()
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
                    },
                    {"type": "text", "text": 'Liệt kê nguyên liệu thực phẩm trong ảnh. Trả về JSON: {"ingredients": ["..."]}'},
                ],
            }],
        )
        return self._parse_json(response.content[0].text)

    async def generate_meal_plan(
        self,
        goal: str,
        days: int,
        calories_target: int,
        persona=None,
        user_note: Optional[str] = None,
    ) -> dict:
        goal_map = {
            "eat_clean": "ăn sạch, lành mạnh",
            "weight_loss": "giảm cân",
            "muscle_gain": "tăng cơ",
            "keto": "Keto",
            "maintenance": "duy trì cân nặng",
        }
        goal_vi = goal_map.get(goal, goal)
        system = (
            f"{persona.meal_plan_prefix} Chỉ trả về JSON."
            if persona and persona.meal_plan_prefix else _DEFAULT_MEAL_PLAN_SYSTEM
        )
        user_note_block = f"\nYêu cầu đặc biệt: {user_note.strip()}" if user_note else ""
        user = f"""Tạo thực đơn {days} ngày, mục tiêu: {goal_vi}, {calories_target} kcal/ngày.{user_note_block}
JSON: {{"plan": [{{"day": 1, "meals": {{"breakfast": "...", "lunch": "...", "dinner": "..."}}}}], "nutrition_summary": {{"avg_calories": {calories_target}, "avg_protein": 100, "avg_carbs": 150, "avg_fat": 50, "notes": "..."}}}}"""
        text = await self._message(system, user)
        logger.debug("anthropic generate_meal_plan done model={}", self._model)
        return self._parse_json(text)

    async def chat(
        self,
        message: str,
        history: list[dict] | None = None,
        persona=None,
    ) -> str:
        system = (
            persona.system_prompt if persona and persona.system_prompt else _DEFAULT_SYSTEM
        )
        messages = []
        if history:
            for msg in history:
                role = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
                parts = msg.get("parts", [])
                messages.append({"role": role, "content": " ".join(parts)})
        messages.append({"role": "user", "content": message})

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    async def classify_intent(self, prompt: str) -> str:
        """Fast structured call for intent classification (temperature=0 for determinism)."""
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=512,
                system="Bạn là hệ thống phân loại ý định. Chỉ trả về JSON, không có text ngoài JSON.",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text or ""
        except Exception as e:
            logger.warning("anthropic classify_intent | error={}", str(e)[:100])
            return ""

    async def extract_memory_facts(self, user_message: str) -> list[dict]:
        from app.services.memory_service import _EXTRACT_PROMPT
        if not user_message or len(user_message.strip()) < 5:
            return []
        try:
            text = await self._message(
                "Bạn là hệ thống extract thông tin. Chỉ trả về JSON array.",
                _EXTRACT_PROMPT.format(message=user_message.strip()),
            )
            raw = self._parse_json(text)
            return [f for f in raw if isinstance(f, dict)] if isinstance(raw, list) else []
        except Exception as e:
            logger.warning("anthropic extract_memory | error={}", str(e)[:100])
            return []
