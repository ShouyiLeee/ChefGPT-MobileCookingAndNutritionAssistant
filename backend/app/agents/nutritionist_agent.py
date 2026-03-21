"""
NutritionistAgent — specializes in nutrition analysis, dietary goal validation, and health advice.

Allowed tools: nutrition analysis, dietary checks, user preferences, recipe search for healthy alternatives.
Default persona: nutrition_expert.

Follows same 3-phase agentic loop as ChefAgent.
"""
from __future__ import annotations

import json
import re
import time

from loguru import logger

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent

_PLAN_PROMPT_TEMPLATE = """\
Bạn là {agent_name} — chuyên gia dinh dưỡng AI.
Người dùng hỏi: "{message}"

Thông tin về người dùng:
{memory_block}

Công cụ có sẵn:
{tools_desc}

Quyết định gọi những công cụ nào (tối đa {max_tools}) để tư vấn dinh dưỡng tốt nhất.
Trả về JSON (không có markdown):
[
  {{"tool": "tên_công_cụ", "args": {{"arg1": "val1"}}, "reason": "lý do"}}
]
Nếu không cần công cụ: []
"""

_SYNTHESIZE_PROMPT_TEMPLATE = """\
Bạn là {system_prompt}

Thông tin về người dùng:
{memory_block}

Người dùng hỏi: "{message}"

Kết quả từ phân tích dinh dưỡng:
{tool_results}

Hãy tư vấn dinh dưỡng một cách chính xác, khoa học và thực tế.
Sử dụng tiếng Việt. Không đề cập đến "công cụ" hay "tool" trong câu trả lời.
"""

_TOOLS_DESCRIPTIONS = {
    "analyze_nutrition": "Ước tính dinh dưỡng (calories, protein, carbs, fat) cho một món ăn",
    "validate_meal_goal": "Kiểm tra thực đơn có phù hợp với mục tiêu sức khỏe không",
    "check_dietary_restrictions": "Kiểm tra công thức có an toàn với hạn chế ăn uống không",
    "get_ingredient_nutrition": "Tra cứu dinh dưỡng của một nguyên liệu cụ thể",
    "get_user_memory_context": "Lấy thông tin ghi nhớ về mục tiêu và hạn chế của người dùng",
    "get_user_preferences": "Lấy danh sách sở thích và hạn chế có cấu trúc",
    "search_community_recipes": "Tìm công thức lành mạnh trong cộng đồng",
}


class NutritionistAgent(BaseAgent):
    """
    Nutrition and dietary advice specialist.
    Handles: calorie counting, macro analysis, dietary restriction checks, meal goal validation.
    """

    ALLOWED_TOOLS = frozenset({
        "analyze_nutrition",
        "validate_meal_goal",
        "check_dietary_restrictions",
        "get_ingredient_nutrition",
        "get_user_memory_context",
        "get_user_preferences",
        "search_community_recipes",
    })
    DEFAULT_PERSONA_ID = "nutrition_expert"

    INTENTS = frozenset({
        "nutrition_analysis",
        "meal_plan_advice",
        "dietary_check",
        "calorie_counting",
    })

    async def execute(self, message: str, context: AgentContext) -> AgentResult:
        from app.core.config import settings

        t0 = time.perf_counter()
        max_iterations = settings.mcp_max_tool_iterations
        logger.info(
            "{} | execute start | message_len={} persona={}",
            self.name, len(message), context.persona.persona_id,
        )

        # ── Phase 1: Planning ──────────────────────────────────────────────────
        tools_desc = "\n".join(
            f"  - {name}: {desc}"
            for name, desc in _TOOLS_DESCRIPTIONS.items()
            if name in self.ALLOWED_TOOLS
        )
        memory_block = context.memory_block or "Không có thông tin đặc biệt."

        plan_prompt = _PLAN_PROMPT_TEMPLATE.format(
            agent_name=self.name,
            message=message[:500],
            memory_block=memory_block[:400],
            tools_desc=tools_desc,
            max_tools=min(3, max_iterations),
        )

        tool_plan: list[dict] = []
        try:
            plan_text = await self._llm.classify_intent(plan_prompt)
            cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", plan_text).strip()
            raw_plan = json.loads(cleaned)
            if isinstance(raw_plan, list):
                tool_plan = raw_plan[:max_iterations]
        except Exception as e:
            logger.warning("{} | planning_error={}", self.name, str(e)[:100])

        logger.debug(
            "{} | plan tools_count={} tools={}",
            self.name, len(tool_plan), [p.get("tool") for p in tool_plan],
        )

        # ── Phase 2: Tool Execution ────────────────────────────────────────────
        tool_results: list[dict] = []
        tools_called: list[str] = []

        for step in tool_plan:
            tool_name = step.get("tool", "")
            tool_args = step.get("args", {})

            if not tool_name or tool_name not in self.ALLOWED_TOOLS:
                continue

            # Inject request-context dependencies
            if tool_name in ("get_user_memory_context", "get_user_preferences"):
                tool_args["user_id"] = context.user_id
                tool_args["db"] = context.db

            try:
                t_tool = time.perf_counter()
                result = await self.call_tool(tool_name, **tool_args)
                tool_ms = round((time.perf_counter() - t_tool) * 1000, 1)
                tool_results.append({"tool": tool_name, "result": result})
                tools_called.append(tool_name)
                logger.info("{} | tool_ok name={} latency={}ms", self.name, tool_name, tool_ms)
            except Exception as e:
                logger.warning("{} | tool_error name={} error={}", self.name, tool_name, str(e)[:100])
                tool_results.append({"tool": tool_name, "error": str(e)[:100]})

        # ── Phase 3: Synthesis ─────────────────────────────────────────────────
        system_prompt = context.persona.system_prompt or (
            "Bạn là chuyên gia dinh dưỡng AI. Tư vấn khoa học, thực tế bằng tiếng Việt."
        )

        results_formatted = (
            json.dumps(
                [{"tool": r["tool"], "data": r.get("result", r.get("error"))}
                 for r in tool_results],
                ensure_ascii=False, indent=2,
            )
            if tool_results else "Không có kết quả từ công cụ."
        )

        synthesize_prompt = _SYNTHESIZE_PROMPT_TEMPLATE.format(
            system_prompt=system_prompt,
            memory_block=memory_block[:400],
            message=message,
            tool_results=results_formatted[:3000],
        )

        try:
            reply = await self._llm.chat(
                synthesize_prompt,
                history=context.history[-6:] if context.history else None,
                persona=context.persona,
            )
        except Exception as e:
            logger.error("{} | synthesis_error={}", self.name, str(e)[:200])
            reply = await self._llm.chat(message, history=context.history, persona=context.persona)

        total_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(
            "{} | done | tools_called={} reply_len={} total_latency={}ms",
            self.name, tools_called, len(reply), total_ms,
        )

        return AgentResult(
            reply=reply,
            tool_calls_made=tools_called,
            structured_data=None,
            agent_name=self.name,
        )
