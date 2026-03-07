"""Gemini 2.5 Flash LLM provider with key rotation and Redis caching."""
import json
import re
import time

from google import genai
from google.genai import types
from loguru import logger

from app.services.cache import CacheService
from app.services.key_manager import GeminiKeyManager
from app.services.llm.base_llm import BaseLLM

_MODEL = "gemini-2.5-flash"

_NO_THINK = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0)
)
_FAST_THINK = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=512)
)


class GeminiLLM(BaseLLM):
    """Gemini 2.5 Flash provider with round-robin key rotation and Redis caching."""

    def __init__(self, key_manager: GeminiKeyManager, cache: CacheService) -> None:
        self._key_manager = key_manager
        self._cache = cache

    # ── Internal helpers ───────────────────────────────────────────────────────

    async def _get_client(self) -> genai.Client:
        key = await self._key_manager.get_key()
        return genai.Client(api_key=key), key

    async def _call(self, fn, *args, retry: bool = True):
        """Call fn(client, *args), handle 429 with key rotation + 1 retry."""
        client, key = await self._get_client()
        t0 = time.perf_counter()
        try:
            result = await fn(client, *args)
            latency = round((time.perf_counter() - t0) * 1000, 1)
            logger.debug("gemini call ok key=...{} latency={}ms", key[-6:], latency)
            return result
        except Exception as e:
            if retry and ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)):
                await self._key_manager.mark_rate_limited(key)
                logger.warning("Gemini 429 on key ...{}, retrying with next key", key[-6:])
                return await self._call(fn, *args, retry=False)
            raise

    @staticmethod
    def _parse_json(text: str) -> dict | list:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
        return json.loads(cleaned)

    # ── Public methods ─────────────────────────────────────────────────────────

    async def suggest_recipes(
        self, ingredients: list[str], filters: list[str] | None = None
    ) -> dict:
        from app.core.config import settings

        cache_key = CacheService.make_key(
            "recipes", ingredients=sorted(ingredients), filters=sorted(filters or [])
        )
        cached = await self._cache.get(cache_key)
        if cached:
            logger.debug("cache hit {}", cache_key)
            return cached

        filters_str = ", ".join(filters) if filters else "không có"
        prompt = f"""Bạn là đầu bếp chuyên nghiệp người Việt.

Nguyên liệu có sẵn: {", ".join(ingredients)}
Yêu cầu/sở thích: {filters_str}

Gợi ý 3 món ăn có thể nấu từ các nguyên liệu trên.
Trả về JSON với cấu trúc sau (không có text ngoài JSON):

{{
  "dishes": [
    {{
      "name": "tên món",
      "description": "mô tả ngắn 1-2 câu",
      "steps": ["bước 1", "bước 2", "..."],
      "time_minutes": 30,
      "difficulty": "easy",
      "nutrition": {{
        "calories": 350,
        "protein": 25,
        "carbs": 40,
        "fat": 10
      }}
    }}
  ]
}}"""

        async def _fn(client, p):
            return await client.aio.models.generate_content(
                model=_MODEL, contents=p, config=_FAST_THINK
            )

        response = await self._call(_fn, prompt)
        result = self._parse_json(response.text)
        await self._cache.set(cache_key, result, settings.cache_ttl_recipes)
        return result

    async def recognize_ingredients(self, image_bytes: bytes) -> dict:
        prompt = (
            "Nhìn vào ảnh và liệt kê tất cả nguyên liệu thực phẩm bạn nhìn thấy. "
            'Trả về JSON (không có text ngoài JSON): {"ingredients": ["nguyên liệu 1", "nguyên liệu 2"]}'
        )
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

        async def _fn(client, p, img):
            return await client.aio.models.generate_content(
                model=_MODEL, contents=[p, img], config=_NO_THINK
            )

        response = await self._call(_fn, prompt, image_part)
        return self._parse_json(response.text)

    async def generate_meal_plan(
        self, goal: str, days: int, calories_target: int
    ) -> dict:
        from app.core.config import settings

        cache_key = CacheService.make_key(
            "mealplan", goal=goal, days=days, calories_target=calories_target
        )
        cached = await self._cache.get(cache_key)
        if cached:
            logger.debug("cache hit {}", cache_key)
            return cached

        goal_map = {
            "eat_clean": "ăn sạch, lành mạnh",
            "weight_loss": "giảm cân",
            "muscle_gain": "tăng cơ",
            "keto": "Keto (ít carb, nhiều chất béo tốt)",
            "maintenance": "duy trì cân nặng",
        }
        goal_vi = goal_map.get(goal, goal)

        prompt = f"""Bạn là chuyên gia dinh dưỡng người Việt.

Tạo thực đơn {days} ngày cho mục tiêu: {goal_vi}
Mục tiêu calories mỗi ngày: {calories_target} kcal

Trả về JSON (không có text ngoài JSON):
{{
  "plan": [
    {{
      "day": 1,
      "meals": {{
        "breakfast": "tên món sáng (calories ước tính)",
        "lunch": "tên món trưa (calories ước tính)",
        "dinner": "tên món tối (calories ước tính)"
      }}
    }}
  ],
  "nutrition_summary": {{
    "avg_calories": {calories_target},
    "avg_protein": 100,
    "avg_carbs": 150,
    "avg_fat": 50,
    "notes": "ghi chú ngắn"
  }}
}}"""

        async def _fn(client, p):
            return await client.aio.models.generate_content(
                model=_MODEL, contents=p, config=_FAST_THINK
            )

        response = await self._call(_fn, prompt)
        result = self._parse_json(response.text)
        await self._cache.set(cache_key, result, settings.cache_ttl_meal_plans)
        return result

    async def chat(self, message: str, history: list[dict] | None = None) -> str:
        system_prompt = (
            "Bạn là ChefGPT — trợ lý nấu ăn và dinh dưỡng AI người Việt. "
            "Trả lời ngắn gọn, thực tế, bằng tiếng Việt. "
            "Chỉ trả lời các câu hỏi liên quan đến nấu ăn, công thức, dinh dưỡng và ẩm thực."
        )
        genai_history = []
        if history:
            for msg in history:
                role = msg.get("role", "user")
                parts = msg.get("parts", [])
                genai_history.append(
                    types.Content(role=role, parts=[types.Part(text=p) for p in parts])
                )

        async def _fn(client, msg, hist, sys_p):
            chat_session = client.chats.create(
                model=_MODEL,
                config=types.GenerateContentConfig(system_instruction=sys_p),
                history=hist,
            )
            return chat_session.send_message(msg)

        response = await self._call(_fn, message, genai_history, system_prompt)
        return response.text
