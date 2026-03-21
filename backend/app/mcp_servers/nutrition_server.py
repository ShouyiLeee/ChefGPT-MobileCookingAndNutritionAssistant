"""
NutritionMCPServer — tools for nutrition analysis and dietary goal validation.

These are new capabilities not previously in the codebase.
All tools use Gemini via structured prompts (thinking_budget=0 for speed).

Tools:
  analyze_nutrition          — estimate macros for a dish
  validate_meal_goal         — check if a meal plan meets nutritional goals
  check_dietary_restrictions — verify recipe safety against user restrictions
  get_ingredient_nutrition   — per-100g nutrition facts for a single ingredient
"""
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.services.llm.base_llm import BaseLLM
    from app.services.tool_registry import ToolRegistry

_NO_THINK_BUDGET = 0


class NutritionMCPServer:
    """MCP server providing nutrition analysis tools powered by Gemini."""

    def __init__(self, llm_provider: "BaseLLM") -> None:
        self._llm = llm_provider

    def register_tools(self, registry: "ToolRegistry") -> None:
        registry.register("analyze_nutrition", self.analyze_nutrition)
        registry.register("validate_meal_goal", self.validate_meal_goal)
        registry.register("check_dietary_restrictions", self.check_dietary_restrictions)
        registry.register("get_ingredient_nutrition", self.get_ingredient_nutrition)
        logger.info("NutritionMCPServer | registered 4 tools")

    # ── Internal helper ────────────────────────────────────────────────────────

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini with no thinking budget. Returns raw text."""
        from google import genai
        from google.genai import types
        from app.core.config import settings

        key = settings.gemini_api_key
        if not key:
            raise RuntimeError("No Gemini API key configured")

        client = genai.Client(api_key=key)
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=_NO_THINK_BUDGET)
        )
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )
        return response.text or ""

    @staticmethod
    def _parse_json(text: str) -> dict | list:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
        return json.loads(cleaned)

    # ── Tools ──────────────────────────────────────────────────────────────────

    async def analyze_nutrition(
        self,
        dish_name: str,
        ingredients: list[str],
        servings: int = 1,
    ) -> dict:
        """
        Estimate nutritional information for a dish.

        Args:
            dish_name: Name of the dish (e.g. "phở bò")
            ingredients: List of ingredient names used
            servings: Number of servings this estimate is for

        Returns:
            {calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg, notes}
        """
        logger.debug(
            "tool:analyze_nutrition | dish={} ingredients_count={} servings={}",
            dish_name, len(ingredients), servings,
        )
        ingredients_str = ", ".join(ingredients) if ingredients else "không rõ"
        prompt = f"""Ước tính dinh dưỡng cho món "{dish_name}" ({servings} phần ăn).
Nguyên liệu chính: {ingredients_str}

Trả về JSON (không có markdown):
{{
  "calories": 450,
  "protein_g": 25,
  "carbs_g": 55,
  "fat_g": 12,
  "fiber_g": 4,
  "sodium_mg": 800,
  "notes": "ghi chú ngắn về dinh dưỡng"
}}"""
        try:
            text = await self._call_gemini(prompt)
            result = self._parse_json(text)
            logger.debug(
                "tool:analyze_nutrition | dish={} calories={} protein={}g",
                dish_name, result.get("calories"), result.get("protein_g"),
            )
            return result
        except Exception as e:
            logger.warning("tool:analyze_nutrition | error={}", str(e)[:100])
            return {"error": str(e)[:100]}

    async def validate_meal_goal(
        self,
        meal_plan: list[dict],
        goal: str,
        daily_calories_target: int,
    ) -> dict:
        """
        Evaluate whether a meal plan aligns with a nutritional goal.

        Args:
            meal_plan: List of day plans [{day: int, meals: {breakfast, lunch, dinner}}]
            goal: Target goal — "weight_loss" | "muscle_gain" | "keto" | "eat_clean" | "maintenance"
            daily_calories_target: Target daily calories

        Returns:
            {is_valid: bool, score: float (0-1), issues: list[str], suggestions: list[str]}
        """
        logger.debug(
            "tool:validate_meal_goal | goal={} days={} target_cal={}",
            goal, len(meal_plan), daily_calories_target,
        )
        goal_map = {
            "weight_loss": "giảm cân",
            "muscle_gain": "tăng cơ",
            "keto": "Keto (ít carb)",
            "eat_clean": "ăn sạch",
            "maintenance": "duy trì cân nặng",
        }
        goal_vi = goal_map.get(goal, goal)

        plan_summary = []
        for day_plan in meal_plan[:7]:  # max 7 days
            day_num = day_plan.get("day", "?")
            meals = day_plan.get("meals", {})
            plan_summary.append(
                f"Ngày {day_num}: Sáng={meals.get('breakfast','?')}, "
                f"Trưa={meals.get('lunch','?')}, Tối={meals.get('dinner','?')}"
            )
        plan_str = "\n".join(plan_summary)

        prompt = f"""Đánh giá thực đơn sau có phù hợp với mục tiêu "{goal_vi}" ({daily_calories_target} kcal/ngày) không.

{plan_str}

Trả về JSON (không có markdown):
{{
  "is_valid": true,
  "score": 0.82,
  "issues": ["danh sách vấn đề nếu có"],
  "suggestions": ["gợi ý cải thiện"]
}}"""
        try:
            text = await self._call_gemini(prompt)
            result = self._parse_json(text)
            logger.debug(
                "tool:validate_meal_goal | goal={} is_valid={} score={}",
                goal, result.get("is_valid"), result.get("score"),
            )
            return result
        except Exception as e:
            logger.warning("tool:validate_meal_goal | error={}", str(e)[:100])
            return {"is_valid": False, "score": 0.0, "issues": [str(e)[:100]], "suggestions": []}

    async def check_dietary_restrictions(
        self,
        recipe_ingredients: list[str],
        user_restrictions: list[str],
    ) -> dict:
        """
        Check if a recipe is safe for a user's dietary restrictions.
        Uses keyword matching first, Gemini for ambiguous cases.

        Args:
            recipe_ingredients: List of ingredient names in the recipe
            user_restrictions: User's known restrictions (e.g. ["tôm", "gluten", "sữa"])

        Returns:
            {safe: bool, conflicts: list[str], substitutions: list[str]}
        """
        logger.debug(
            "tool:check_dietary_restrictions | ingredients={} restrictions={}",
            len(recipe_ingredients), user_restrictions,
        )
        if not user_restrictions:
            return {"safe": True, "conflicts": [], "substitutions": []}

        # Fast keyword check first
        ingredients_lower = [i.lower() for i in recipe_ingredients]
        direct_conflicts = []
        for restriction in user_restrictions:
            r_lower = restriction.lower()
            for ingredient in ingredients_lower:
                if r_lower in ingredient or ingredient in r_lower:
                    direct_conflicts.append(f"{ingredient} ({restriction})")
                    break

        if direct_conflicts:
            # Ask Gemini for substitutions
            conflicts_str = ", ".join(direct_conflicts)
            prompt = f"""Recipe có các nguyên liệu sau bị xung đột với hạn chế ăn uống: {conflicts_str}
Gợi ý thay thế ngắn gọn.

Trả về JSON:
{{
  "safe": false,
  "conflicts": {json.dumps(direct_conflicts, ensure_ascii=False)},
  "substitutions": ["thay X bằng Y", "bỏ Z hoặc dùng W"]
}}"""
            try:
                text = await self._call_gemini(prompt)
                result = self._parse_json(text)
                return result
            except Exception:
                return {"safe": False, "conflicts": direct_conflicts, "substitutions": []}

        # No direct conflicts — do a quick Gemini semantic check for hidden allergens
        ingredients_str = ", ".join(recipe_ingredients[:20])
        restrictions_str = ", ".join(user_restrictions)
        prompt = f"""Kiểm tra xem recipe với nguyên liệu "{ingredients_str}" có an toàn cho người có hạn chế: {restrictions_str} không.
Chỉ xét các nguyên liệu ẩn (ví dụ: nước mắm chứa cá, bột mì chứa gluten).

Trả về JSON:
{{
  "safe": true,
  "conflicts": [],
  "substitutions": []
}}"""
        try:
            text = await self._call_gemini(prompt)
            return self._parse_json(text)
        except Exception as e:
            logger.warning("tool:check_dietary_restrictions | error={}", str(e)[:80])
            return {"safe": True, "conflicts": [], "substitutions": []}

    async def get_ingredient_nutrition(
        self,
        ingredient: str,
        amount_grams: int = 100,
    ) -> dict:
        """
        Get nutrition facts for a single ingredient.

        Args:
            ingredient: Ingredient name (e.g. "thịt bò", "cà rốt")
            amount_grams: Amount in grams

        Returns:
            {calories, protein_g, carbs_g, fat_g, fiber_g}
        """
        logger.debug(
            "tool:get_ingredient_nutrition | ingredient={} amount={}g",
            ingredient, amount_grams,
        )
        prompt = f"""Giá trị dinh dưỡng của {amount_grams}g "{ingredient}".

Trả về JSON (không có markdown):
{{
  "ingredient": "{ingredient}",
  "amount_grams": {amount_grams},
  "calories": 150,
  "protein_g": 20,
  "carbs_g": 0,
  "fat_g": 7,
  "fiber_g": 0
}}"""
        try:
            text = await self._call_gemini(prompt)
            return self._parse_json(text)
        except Exception as e:
            logger.warning("tool:get_ingredient_nutrition | error={}", str(e)[:100])
            return {"error": str(e)[:100]}
