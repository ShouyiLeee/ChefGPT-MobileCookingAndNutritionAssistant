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

    async def _get_client(self):
        key = await self._key_manager.get_key()
        return genai.Client(api_key=key), key

    async def _call(self, fn, *args, retry: bool = True, operation: str = "unknown"):
        """Call fn(client, *args), handle 429 with key rotation + 1 retry."""
        client, key = await self._get_client()
        t0 = time.perf_counter()
        try:
            result = await fn(client, *args)
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            usage = getattr(getattr(result, "usage_metadata", None), "__dict__", {})
            logger.info(
                "llm_call | op={} model={} key=...{} latency={}ms prompt_tokens={} output_tokens={}",
                operation, _MODEL, key[-6:], latency_ms,
                usage.get("prompt_token_count", "?"),
                usage.get("candidates_token_count", "?"),
            )
            return result
        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            err_str = str(e)
            if retry and ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str):
                await self._key_manager.mark_rate_limited(key)
                logger.warning(
                    "llm_rate_limited | op={} key=...{} latency={}ms retrying=true",
                    operation, key[-6:], latency_ms,
                )
                return await self._call(fn, *args, retry=False, operation=operation)
            logger.error(
                "llm_error | op={} key=...{} latency={}ms error={}",
                operation, key[-6:], latency_ms, err_str[:200],
            )
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
        from app.services.rag import rag_service

        t_total = time.perf_counter()
        _filters = filters or []
        logger.info(
            "suggest_recipes | ingredients_count={} ingredients={} filters={}",
            len(ingredients), ingredients, _filters,
        )

        cache_key = CacheService.make_key(
            "recipes", ingredients=sorted(ingredients), filters=sorted(_filters)
        )
        cached = await self._cache.get(cache_key)
        if cached:
            logger.info(
                "suggest_recipes | cache=HIT key_suffix={} dishes_count={}",
                cache_key[-12:], len(cached.get("dishes", [])),
            )
            return cached

        t_rag = time.perf_counter()
        rag_context = await rag_service.get_context(ingredients, _filters)
        logger.debug(
            "suggest_recipes | rag_search latency={}ms has_context={} context_len={}",
            round((time.perf_counter() - t_rag) * 1000, 1), bool(rag_context), len(rag_context),
        )

        filters_str = ", ".join(_filters) if _filters else "không có"
        rag_block = f"\n{rag_context}\n" if rag_context else ""
        prompt = f"""Bạn là đầu bếp chuyên nghiệp người Việt.
{rag_block}
Nguyên liệu có sẵn: {", ".join(ingredients)}
Yêu cầu/sở thích: {filters_str}

Gợi ý 3 món ăn có thể nấu từ các nguyên liệu trên (tham khảo công thức cộng đồng ở trên nếu phù hợp, nhưng hãy sáng tạo và điều chỉnh theo nguyên liệu hiện có).
Trả về JSON với cấu trúc sau (không có text ngoài JSON):

{{
  "dishes": [
    {{
      "name": "tên món",
      "description": "mô tả ngắn 1-2 câu",
      "steps": ["bước 1", "bước 2", "..."],
      "time_minutes": 30,
      "difficulty": "easy",
      "nutrition": {{"calories": 350, "protein": 25, "carbs": 40, "fat": 10}}
    }}
  ]
}}"""

        async def _fn(client, p):
            return await client.aio.models.generate_content(
                model=_MODEL, contents=p, config=_FAST_THINK
            )

        response = await self._call(_fn, prompt, operation="suggest_recipes")
        result = self._parse_json(response.text)
        dishes = result.get("dishes", [])
        dish_names = [d.get("name", "?") for d in dishes]
        await self._cache.set(cache_key, result, settings.cache_ttl_recipes)

        total_ms = round((time.perf_counter() - t_total) * 1000, 1)
        logger.info(
            "suggest_recipes | cache=MISS dishes_count={} dishes={} rag_used={} total_latency={}ms ttl={}s",
            len(dishes), dish_names, bool(rag_context), total_ms, settings.cache_ttl_recipes,
        )
        return result

    async def recognize_ingredients(self, image_bytes: bytes) -> dict:
        image_kb = round(len(image_bytes) / 1024, 1)
        logger.info("recognize_ingredients | image_size={}KB", image_kb)

        prompt = (
            "Nhìn vào ảnh và liệt kê tất cả nguyên liệu thực phẩm bạn nhìn thấy. "
            'Trả về JSON (không có text ngoài JSON): {"ingredients": ["nguyên liệu 1", "nguyên liệu 2"]}'
        )
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

        async def _fn(client, p, img):
            return await client.aio.models.generate_content(
                model=_MODEL, contents=[p, img], config=_NO_THINK
            )

        t0 = time.perf_counter()
        response = await self._call(_fn, prompt, image_part, operation="recognize_ingredients")
        result = self._parse_json(response.text)
        found = result.get("ingredients", [])
        logger.info(
            "recognize_ingredients | ingredients_found={} ingredients={} latency={}ms",
            len(found), found, round((time.perf_counter() - t0) * 1000, 1),
        )
        return result

    async def generate_meal_plan(self, goal: str, days: int, calories_target: int) -> dict:
        from app.core.config import settings

        t_total = time.perf_counter()
        logger.info(
            "generate_meal_plan | goal={} days={} calories_target={}",
            goal, days, calories_target,
        )

        cache_key = CacheService.make_key(
            "mealplan", goal=goal, days=days, calories_target=calories_target
        )
        cached = await self._cache.get(cache_key)
        if cached:
            plan_days = len(cached.get("plan", []))
            logger.info(
                "generate_meal_plan | cache=HIT key_suffix={} plan_days={}",
                cache_key[-12:], plan_days,
            )
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

        response = await self._call(_fn, prompt, operation="generate_meal_plan")
        result = self._parse_json(response.text)

        plan_days = len(result.get("plan", []))
        nutrition = result.get("nutrition_summary", {})
        await self._cache.set(cache_key, result, settings.cache_ttl_meal_plans)

        total_ms = round((time.perf_counter() - t_total) * 1000, 1)
        logger.info(
            "generate_meal_plan | cache=MISS plan_days={} avg_calories={} avg_protein={}g avg_carbs={}g avg_fat={}g total_latency={}ms",
            plan_days,
            nutrition.get("avg_calories", "?"),
            nutrition.get("avg_protein", "?"),
            nutrition.get("avg_carbs", "?"),
            nutrition.get("avg_fat", "?"),
            total_ms,
        )
        return result

    async def chat(self, message: str, history: list[dict] | None = None) -> str:
        history_turns = len(history) if history else 0
        logger.info("chat | message_len={} history_turns={}", len(message), history_turns)

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
            chat_session = client.aio.chats.create(
                model=_MODEL,
                config=types.GenerateContentConfig(system_instruction=sys_p),
                history=hist,
            )
            return await chat_session.send_message(msg)

        t0 = time.perf_counter()
        response = await self._call(_fn, message, genai_history, system_prompt, operation="chat")
        reply_text = response.text

        logger.info(
            "chat | response_len={} latency={}ms",
            len(reply_text), round((time.perf_counter() - t0) * 1000, 1),
        )
        return reply_text
