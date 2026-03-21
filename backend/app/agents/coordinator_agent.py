"""
CoordinatorAgent — intent classifier and request router.

Does NOT generate a user-facing reply.
Uses Gemini with thinking_budget=0 (~100ms) for fast intent classification.
Returns a RoutingDecision that tells AgenticLoop which agent(s) to dispatch to.

Intent taxonomy:
  chef      — recipe_suggestion, cooking_technique, ingredient_recognition, recipe_detail, general_chat
  nutritionist — nutrition_analysis, meal_plan_advice, dietary_check, calorie_counting
  shopping  — shopping_intent, grocery_list, ingredient_sourcing, budget_planning
  combined_recipe_shopping — chef + shopping running in parallel
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.services.llm.base_llm import BaseLLM


_CLASSIFY_PROMPT_TEMPLATE = """\
Phân tích câu hỏi của người dùng và xác định loại yêu cầu.

Câu hỏi: "{message}"

Thông tin người dùng:
{memory_block}

Các loại yêu cầu:
- "recipe_suggestion" — gợi ý món ăn, công thức, nấu gì với nguyên liệu
- "cooking_technique" — hỏi cách nấu, kỹ thuật nấu ăn
- "ingredient_recognition" — nhận diện nguyên liệu từ ảnh
- "recipe_detail" — hỏi chi tiết công thức cụ thể
- "nutrition_analysis" — hỏi dinh dưỡng, calories của món ăn
- "meal_plan_advice" — tư vấn thực đơn theo mục tiêu sức khỏe
- "dietary_check" — kiểm tra dị ứng, thực phẩm phù hợp
- "calorie_counting" — đếm calo, tính dinh dưỡng
- "shopping_intent" — muốn mua nguyên liệu, đặt hàng
- "grocery_list" — lập danh sách mua sắm
- "ingredient_sourcing" — hỏi mua nguyên liệu ở đâu
- "budget_planning" — hỏi giá cả, lên kế hoạch chi tiêu
- "combined_recipe_shopping" — vừa muốn gợi ý món VÀ mua nguyên liệu
- "general_chat" — hỏi thăm, nói chuyện chung về ẩm thực

Trả về JSON (không có markdown):
{{
  "intent": "loại_yêu_cầu",
  "primary_agent": "chef" hoặc "nutritionist" hoặc "shopping",
  "secondary_agents": [],
  "confidence": 0.95
}}

Quy tắc chọn agent:
- intent recipe/cooking/ingredient/general → primary_agent = "chef"
- intent nutrition/meal_plan/dietary → primary_agent = "nutritionist"
- intent shopping/grocery/sourcing/budget → primary_agent = "shopping"
- intent combined_recipe_shopping → primary_agent = "chef", secondary_agents = ["shopping"]
"""

# Mapping intent → primary agent (fallback for parse failures)
_INTENT_AGENT_MAP: dict[str, tuple[str, list[str]]] = {
    "recipe_suggestion":        ("chef", []),
    "cooking_technique":        ("chef", []),
    "ingredient_recognition":   ("chef", []),
    "recipe_detail":            ("chef", []),
    "general_chat":             ("chef", []),
    "nutrition_analysis":       ("nutritionist", []),
    "meal_plan_advice":         ("nutritionist", []),
    "dietary_check":            ("nutritionist", []),
    "calorie_counting":         ("nutritionist", []),
    "shopping_intent":          ("shopping", []),
    "grocery_list":             ("shopping", []),
    "ingredient_sourcing":      ("shopping", []),
    "budget_planning":          ("shopping", []),
    "combined_recipe_shopping": ("chef", ["shopping"]),
}


@dataclass
class RoutingDecision:
    """Result of CoordinatorAgent.classify()."""
    primary_agent: str              # "chef" | "nutritionist" | "shopping"
    secondary_agents: list[str] = field(default_factory=list)  # run in parallel with primary
    intent: str = "general_chat"
    confidence: float = 1.0


class CoordinatorAgent:
    """
    Lightweight intent classifier.
    Uses Gemini thinking_budget=0 — target latency ~100-150ms.
    Should be initialized once and reused (stateless).
    """

    def __init__(self, llm: "BaseLLM") -> None:
        self._llm = llm

    async def classify(
        self,
        message: str,
        history: list[dict] | None = None,
        memory_block: str = "",
    ) -> RoutingDecision:
        """
        Classify a user message and return a RoutingDecision.
        Falls back to chef agent on any error.
        """
        t0 = time.perf_counter()
        logger.debug("coordinator | classify message_len={}", len(message))

        prompt = _CLASSIFY_PROMPT_TEMPLATE.format(
            message=message[:500],
            memory_block=memory_block[:200] if memory_block else "Không có",
        )

        try:
            raw_text = await self._llm.classify_intent(prompt)
            cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw_text).strip()
            data = json.loads(cleaned)

            intent = data.get("intent", "general_chat")
            primary = data.get("primary_agent", "chef")
            secondary = data.get("secondary_agents", [])
            confidence = float(data.get("confidence", 1.0))

            # Validate agent names
            valid_agents = {"chef", "nutritionist", "shopping"}
            if primary not in valid_agents:
                primary = "chef"
            secondary = [a for a in secondary if a in valid_agents and a != primary]

            decision = RoutingDecision(
                primary_agent=primary,
                secondary_agents=secondary,
                intent=intent,
                confidence=confidence,
            )
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.info(
                "coordinator | intent={} primary={} secondary={} confidence={:.2f} latency={}ms",
                intent, primary, secondary, confidence, latency_ms,
            )
            return decision

        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.warning(
                "coordinator | classify_error={} latency={}ms — defaulting to chef",
                str(e)[:100], latency_ms,
            )
            return RoutingDecision(primary_agent="chef", intent="general_chat", confidence=0.5)
