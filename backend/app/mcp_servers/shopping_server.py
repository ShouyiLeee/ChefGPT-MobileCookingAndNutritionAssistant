"""
ShoppingMCPServer — tools for shopping intent detection, cart building, and grocery planning.

Tools:
  detect_shopping_intent    — detect if a message has purchase intent
  build_shopping_cart       — build a CartMandate from detected intent
  optimize_grocery_list     — extract & consolidate ingredients from a recipe list
  find_ingredient_substitutes — suggest substitutes for unavailable/allergenic ingredients
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.services.llm.base_llm import BaseLLM
    from app.services.shopping_agent import ShoppingAgentService
    from app.services.tool_registry import ToolRegistry


class ShoppingMCPServer:
    """MCP server wrapping shopping and grocery operations."""

    def __init__(
        self,
        shopping_agent_service: "ShoppingAgentService",
        llm_provider: "BaseLLM",
    ) -> None:
        self._shopping = shopping_agent_service
        self._llm = llm_provider

    def register_tools(self, registry: "ToolRegistry") -> None:
        registry.register("detect_shopping_intent", self.detect_shopping_intent)
        registry.register("build_shopping_cart", self.build_shopping_cart)
        registry.register("optimize_grocery_list", self.optimize_grocery_list)
        registry.register("find_ingredient_substitutes", self.find_ingredient_substitutes)
        logger.info("ShoppingMCPServer | registered 4 tools")

    # ── Tools ──────────────────────────────────────────────────────────────────

    async def detect_shopping_intent(self, message: str) -> dict:
        """
        Detect if a user message contains shopping intent for food ingredients.

        Args:
            message: The user's chat message

        Returns:
            {has_intent: bool, items_mentioned: list[str], suggested_store: str | None}
        """
        logger.debug("tool:detect_shopping_intent | message_len={}", len(message))
        result = await self._shopping.detect_shopping_intent(message)
        if result is None:
            return {"has_intent": False, "items_mentioned": [], "suggested_store": None}
        return {
            "has_intent": result.has_intent,
            "items_mentioned": result.items_mentioned,
            "suggested_store": result.suggested_store,
        }

    async def build_shopping_cart(
        self,
        items_mentioned: list[str],
        budget_limit: float | None = None,
        suggested_store: str | None = None,
    ) -> dict:
        """
        Build a cart mandate from detected shopping items.
        Fuzzy-matches against products.json, picks best store.

        Args:
            items_mentioned: List of ingredient/product names to buy
            budget_limit: Optional max total in k VND (items are not dropped but flagged)
            suggested_store: Optional preferred store_id

        Returns:
            CartMandate dict with {store_id, store_name, items, subtotal, delivery_fee, estimated_total}
        """
        from app.services.shopping_agent import ShoppingIntentResult

        logger.debug(
            "tool:build_shopping_cart | items={} budget={} store={}",
            items_mentioned, budget_limit, suggested_store,
        )
        intent = ShoppingIntentResult(
            has_intent=True,
            items_mentioned=items_mentioned,
            suggested_store=suggested_store,
        )
        cart = await self._shopping.build_cart_from_intent(intent)

        result = {
            "store_id": cart.store_id,
            "store_name": cart.store_name,
            "items": [
                {
                    "product_id": i.product_id,
                    "product_name": i.product_name,
                    "product_emoji": i.product_emoji,
                    "unit": i.unit,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "subtotal": i.subtotal,
                }
                for i in cart.items
            ],
            "subtotal": cart.subtotal,
            "delivery_fee": cart.delivery_fee,
            "estimated_total": cart.estimated_total,
            "intent_description": cart.intent_description,
            "over_budget": (
                cart.estimated_total > budget_limit if budget_limit else False
            ),
        }
        logger.info(
            "tool:build_shopping_cart | store={} items={} total={}k over_budget={}",
            cart.store_id, len(cart.items), cart.estimated_total, result["over_budget"],
        )
        return result

    async def optimize_grocery_list(
        self,
        recipe_list: list[str],
        servings_per_meal: int = 4,
    ) -> dict:
        """
        Given a list of recipe names, extract and consolidate ingredients
        into a single optimized grocery list with estimated costs.

        Args:
            recipe_list: List of dish names (e.g. ["phở bò", "cơm tấm sườn"])
            servings_per_meal: Number of servings per dish

        Returns:
            {ingredients: [{name, quantity, unit, estimated_cost_k}], total_estimated_cost_k}
        """
        from google import genai
        from google.genai import types
        from app.core.config import settings

        logger.debug(
            "tool:optimize_grocery_list | recipes={} servings={}",
            recipe_list, servings_per_meal,
        )

        if not recipe_list:
            return {"ingredients": [], "total_estimated_cost_k": 0}

        recipes_str = "\n".join(f"- {r}" for r in recipe_list)
        prompt = f"""Bạn là chuyên gia mua sắm thực phẩm. Với danh sách món ăn dưới đây ({servings_per_meal} phần ăn mỗi món), hãy tạo danh sách nguyên liệu mua sắm tổng hợp.

Danh sách món:
{recipes_str}

Gộp các nguyên liệu trùng lặp, ước tính số lượng cần thiết và giá tham khảo (VND).

Trả về JSON (không có markdown):
{{
  "ingredients": [
    {{"name": "tên nguyên liệu", "quantity": 500, "unit": "g", "estimated_cost_k": 15}}
  ],
  "total_estimated_cost_k": 120
}}"""

        key = settings.gemini_api_key
        if not key:
            return {"ingredients": [], "total_estimated_cost_k": 0, "error": "No API key"}

        try:
            client = genai.Client(api_key=key)
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            import json, re
            text = re.sub(r"```(?:json)?\s*|\s*```", "", response.text or "").strip()
            return json.loads(text)
        except Exception as e:
            logger.warning("tool:optimize_grocery_list | error={}", str(e)[:100])
            return {"ingredients": [], "total_estimated_cost_k": 0, "error": str(e)[:100]}

    async def find_ingredient_substitutes(
        self,
        ingredient: str,
        reason: str = "unavailable",
    ) -> list[dict]:
        """
        Suggest substitutes for an ingredient that is unavailable, allergenic, or costly.

        Args:
            ingredient: Ingredient name (e.g. "tôm", "bơ")
            reason: Why substitution is needed — "unavailable" | "allergy" | "budget" | "vegan"

        Returns:
            List of {substitute, notes, nutrition_change}
        """
        from google import genai
        from google.genai import types
        from app.core.config import settings

        logger.debug(
            "tool:find_ingredient_substitutes | ingredient={} reason={}",
            ingredient, reason,
        )

        reason_map = {
            "unavailable": "không có sẵn",
            "allergy": "dị ứng",
            "budget": "giá quá cao",
            "vegan": "ăn chay",
        }
        reason_vi = reason_map.get(reason, reason)

        prompt = f"""Gợi ý 3 nguyên liệu thay thế cho "{ingredient}" vì lý do: {reason_vi}.

Trả về JSON (không có markdown):
[
  {{
    "substitute": "tên nguyên liệu thay thế",
    "notes": "cách dùng và lưu ý ngắn",
    "nutrition_change": "ảnh hưởng dinh dưỡng (ví dụ: ít protein hơn 30%)"
  }}
]"""

        key = settings.gemini_api_key
        if not key:
            return []

        try:
            client = genai.Client(api_key=key)
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            import json, re
            text = re.sub(r"```(?:json)?\s*|\s*```", "", response.text or "").strip()
            result = json.loads(text)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.warning("tool:find_ingredient_substitutes | error={}", str(e)[:100])
            return []
