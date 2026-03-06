"""GeminiService — single entry point for all AI calls via Gemini 2.5 Flash."""
import json
import re

from google import genai
from google.genai import types

from app.core.config import settings

_MODEL = "gemini-2.5-flash"

# Disable thinking for fast vision/simple tasks (no reasoning needed)
_NO_THINK = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0)
)

# Minimal thinking for recipe/meal plan generation
_FAST_THINK = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=512)
)


class GeminiService:
    """Wrapper around Gemini 2.5 Flash for all ChefGPT AI features."""

    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def _parse_json(self, text: str) -> dict | list:
        """Extract and parse JSON from model response."""
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
        return json.loads(cleaned)

    async def suggest_recipes(
        self, ingredients: list[str], filters: list[str] | None = None
    ) -> dict:
        """Suggest dishes based on available ingredients."""
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
        response = await self.client.aio.models.generate_content(
            model=_MODEL, contents=prompt, config=_FAST_THINK
        )
        return self._parse_json(response.text)

    async def recognize_ingredients(self, image_bytes: bytes) -> dict:
        """Recognize food ingredients from an image (thinking disabled for speed)."""
        prompt = 'Nhìn vào ảnh và liệt kê tất cả nguyên liệu thực phẩm bạn nhìn thấy. Trả về JSON (không có text ngoài JSON): {"ingredients": ["nguyên liệu 1", "nguyên liệu 2"]}'
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        response = await self.client.aio.models.generate_content(
            model=_MODEL, contents=[prompt, image_part], config=_NO_THINK
        )
        return self._parse_json(response.text)

    async def generate_meal_plan(
        self, goal: str, days: int, calories_target: int
    ) -> dict:
        """Generate a meal plan based on user goal."""
        goal_map = {
            "eat_clean": "ăn sạch, lành mạnh",
            "weight_loss": "giảm cân",
            "muscle_gain": "tăng cơ",
            "keto": "Keto (ít carb, nhiều chất béo tốt)",
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
        response = self.client.models.generate_content(model=_MODEL, contents=prompt)
        return self._parse_json(response.text)

    async def chat(self, message: str, history: list[dict] | None = None) -> str:
        """General cooking/nutrition chat."""
        system_prompt = (
            "Bạn là ChefGPT — trợ lý nấu ăn và dinh dưỡng AI người Việt. "
            "Trả lời ngắn gọn, thực tế, bằng tiếng Việt. "
            "Chỉ trả lời các câu hỏi liên quan đến nấu ăn, công thức, dinh dưỡng và ẩm thực."
        )
        # Convert history to genai format
        genai_history = []
        if history:
            for msg in history:
                role = msg.get("role", "user")
                parts = msg.get("parts", [])
                genai_history.append(types.Content(role=role, parts=[types.Part(text=p) for p in parts]))

        chat_session = self.client.chats.create(
            model=_MODEL,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
            history=genai_history,
        )
        response = chat_session.send_message(message)
        return response.text


# Singleton instance
gemini_service = GeminiService()
