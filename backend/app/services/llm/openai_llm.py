"""OpenAI GPT provider (optional — set LLM_PROVIDER=openai)."""
import json

from loguru import logger

from app.services.llm.base_llm import BaseLLM


class OpenAILLM(BaseLLM):
    """GPT-4o-mini provider. Requires `openai` package and OPENAI_API_KEY."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package not installed — run: pip install openai>=1.30.0")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def _chat_completion(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.7,
        )
        return response.choices[0].message.content

    @staticmethod
    def _parse_json(text: str) -> dict | list:
        import re
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
        return json.loads(cleaned)

    async def suggest_recipes(
        self, ingredients: list[str], filters: list[str] | None = None
    ) -> dict:
        filters_str = ", ".join(filters) if filters else "không có"
        system = "Bạn là đầu bếp chuyên nghiệp người Việt. Chỉ trả về JSON, không có text ngoài JSON."
        user = f"""Nguyên liệu: {", ".join(ingredients)}
Yêu cầu: {filters_str}

Gợi ý 3 món, trả về JSON:
{{"dishes": [{{"name": "...", "description": "...", "steps": ["..."], "time_minutes": 30, "difficulty": "easy", "nutrition": {{"calories": 350, "protein": 25, "carbs": 40, "fat": 10}}}}]}}"""
        text = await self._chat_completion(system, user)
        logger.debug("openai suggest_recipes done model={}", self._model)
        return self._parse_json(text)

    async def recognize_ingredients(self, image_bytes: bytes) -> dict:
        import base64
        from openai import AsyncOpenAI

        b64 = base64.b64encode(image_bytes).decode()
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": 'Liệt kê nguyên liệu thực phẩm trong ảnh. Trả về JSON: {"ingredients": ["..."]}'},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }],
        )
        return self._parse_json(response.choices[0].message.content)

    async def generate_meal_plan(
        self, goal: str, days: int, calories_target: int
    ) -> dict:
        goal_map = {
            "eat_clean": "ăn sạch, lành mạnh",
            "weight_loss": "giảm cân",
            "muscle_gain": "tăng cơ",
            "keto": "Keto",
            "maintenance": "duy trì cân nặng",
        }
        goal_vi = goal_map.get(goal, goal)
        system = "Bạn là chuyên gia dinh dưỡng người Việt. Chỉ trả về JSON."
        user = f"""Tạo thực đơn {days} ngày, mục tiêu: {goal_vi}, {calories_target} kcal/ngày.
JSON: {{"plan": [{{"day": 1, "meals": {{"breakfast": "...", "lunch": "...", "dinner": "..."}}}}], "nutrition_summary": {{"avg_calories": {calories_target}, "avg_protein": 100, "avg_carbs": 150, "avg_fat": 50, "notes": "..."}}}}"""
        text = await self._chat_completion(system, user)
        logger.debug("openai generate_meal_plan done model={}", self._model)
        return self._parse_json(text)

    async def chat(self, message: str, history: list[dict] | None = None) -> str:
        messages = [{
            "role": "system",
            "content": (
                "Bạn là ChefGPT — trợ lý nấu ăn và dinh dưỡng AI người Việt. "
                "Trả lời ngắn gọn, thực tế, bằng tiếng Việt."
            ),
        }]
        if history:
            for msg in history:
                role = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
                parts = msg.get("parts", [])
                messages.append({"role": role, "content": " ".join(parts)})
        messages.append({"role": "user", "content": message})

        response = await self._client.chat.completions.create(
            model=self._model, messages=messages, temperature=0.7
        )
        return response.choices[0].message.content
