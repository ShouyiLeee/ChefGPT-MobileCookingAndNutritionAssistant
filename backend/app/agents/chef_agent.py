"""
ChefAgent — specializes in recipe suggestion, cooking techniques, and ingredient recognition.

Allowed tools: recipe search, RAG, vision, ingredient substitution, user memory.
Default persona: asian_chef (Vietnamese cuisine specialist).

3-phase agentic loop:
  Phase 1 — Planning    (thinking_budget=512): Decide which tools to call
  Phase 2 — Execution:  Call each tool via self.call_tool()
  Phase 3 — Synthesis   (thinking_budget=1024): Generate final response with tool results
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from loguru import logger

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent

_PLAN_PROMPT_TEMPLATE = """\
Bạn là {agent_name} — trợ lý nấu ăn thông minh.
Người dùng hỏi: "{message}"

Thông tin về người dùng:
{memory_block}

Công cụ có sẵn:
{tools_desc}

Quyết định gọi những công cụ nào (tối đa {max_tools}) để trả lời tốt nhất.
Trả về JSON (không có markdown):
[
  {{"tool": "tên_công_cụ", "args": {{"arg1": "val1"}}, "reason": "lý do ngắn"}}
]
Nếu không cần công cụ nào, trả về: []
"""

_SYNTHESIZE_PROMPT_TEMPLATE = """\
Bạn là {system_prompt}

Thông tin về người dùng:
{memory_block}

Người dùng hỏi: "{message}"

Kết quả từ các công cụ:
{tool_results}

Hãy trả lời người dùng một cách hữu ích, cụ thể và thân thiện dựa trên kết quả trên.
Sử dụng tiếng Việt. Không đề cập đến "công cụ" hay "tool" trong câu trả lời.
"""

_TOOLS_DESCRIPTIONS = {
    "search_community_recipes": "Tìm kiếm công thức trong cộng đồng theo từ khóa, ẩm thực, hoặc độ khó",
    "get_community_recipe_detail": "Lấy chi tiết đầy đủ một công thức theo id",
    "suggest_recipes_from_ingredients": "Gợi ý món ăn từ danh sách nguyên liệu có sẵn",
    "save_recipe": "Lưu một công thức vào danh sách yêu thích của người dùng",
    "list_saved_recipes": "Xem danh sách công thức đã lưu của người dùng",
    "recognize_ingredients_from_image": "Nhận diện nguyên liệu từ ảnh",
    "analyze_food_image": "Phân tích ảnh thực phẩm: tên món, nguyên liệu, dinh dưỡng",
    "find_ingredient_substitutes": "Gợi ý nguyên liệu thay thế khi không có hoặc dị ứng",
    "get_user_memory_context": "Lấy thông tin ghi nhớ về sở thích/hạn chế của người dùng",
}


class ChefAgent(BaseAgent):
    """
    Recipe and cooking specialist agent.
    Handles: recipe suggestions, cooking techniques, ingredient identification, ingredient substitution.
    """

    ALLOWED_TOOLS = frozenset({
        "search_community_recipes",
        "get_community_recipe_detail",
        "suggest_recipes_from_ingredients",
        "save_recipe",
        "list_saved_recipes",
        "recognize_ingredients_from_image",
        "analyze_food_image",
        "find_ingredient_substitutes",
        "get_user_memory_context",
    })
    DEFAULT_PERSONA_ID = "asian_chef"

    INTENTS = frozenset({
        "recipe_suggestion",
        "cooking_technique",
        "ingredient_recognition",
        "recipe_detail",
        "general_chat",
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
            logger.warning("{} | planning_error={} — proceeding without tools", self.name, str(e)[:100])

        logger.debug("{} | plan tools_count={} tools={}", self.name, len(tool_plan), [p.get("tool") for p in tool_plan])

        # ── Phase 2: Tool Execution ────────────────────────────────────────────
        tool_results: list[dict] = []
        tools_called: list[str] = []
        structured_data: dict | None = None

        for step in tool_plan:
            tool_name = step.get("tool", "")
            tool_args = step.get("args", {})
            reason = step.get("reason", "")

            if not tool_name or tool_name not in self.ALLOWED_TOOLS:
                logger.debug("{} | skip unknown tool={}", self.name, tool_name)
                continue

            # Inject non-LLM-visible context (user_id, db) for tools that need them
            if tool_name in ("save_recipe", "list_saved_recipes"):
                tool_args["user_id"] = context.user_id
                tool_args["db"] = context.db
            elif tool_name == "get_user_memory_context":
                tool_args["user_id"] = context.user_id
                tool_args["db"] = context.db

            try:
                t_tool = time.perf_counter()
                result = await self.call_tool(tool_name, **tool_args)
                tool_ms = round((time.perf_counter() - t_tool) * 1000, 1)
                tool_results.append({
                    "tool": tool_name,
                    "result": result,
                    "reason": reason,
                })
                tools_called.append(tool_name)
                logger.info(
                    "{} | tool_ok name={} latency={}ms",
                    self.name, tool_name, tool_ms,
                )
                # Capture structured shopping data if present
                if tool_name == "build_shopping_cart" and isinstance(result, dict):
                    structured_data = {"cart": result}
            except Exception as e:
                logger.warning("{} | tool_error name={} error={}", self.name, tool_name, str(e)[:100])
                tool_results.append({"tool": tool_name, "error": str(e)[:100]})

        # ── Phase 3: Synthesis ─────────────────────────────────────────────────
        system_prompt = context.persona.system_prompt or (
            "Bạn là ChefGPT — trợ lý nấu ăn và dinh dưỡng AI người Việt. "
            "Trả lời ngắn gọn, thực tế, bằng tiếng Việt."
        )

        if tool_results:
            results_formatted = json.dumps(
                [{"tool": r["tool"], "data": r.get("result", r.get("error"))}
                 for r in tool_results],
                ensure_ascii=False, indent=2
            )
        else:
            results_formatted = "Không có kết quả từ công cụ."

        synthesize_prompt = _SYNTHESIZE_PROMPT_TEMPLATE.format(
            system_prompt=system_prompt,
            memory_block=memory_block[:400],
            message=message,
            tool_results=results_formatted[:3000],
        )

        try:
            # Use chat() for synthesis — it uses persona system_prompt correctly
            reply = await self._llm.chat(
                synthesize_prompt,
                history=context.history[-6:] if context.history else None,
                persona=context.persona,
            )
        except Exception as e:
            logger.error("{} | synthesis_error={}", self.name, str(e)[:200])
            # Fallback: direct chat without tool context
            reply = await self._llm.chat(message, history=context.history, persona=context.persona)

        total_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(
            "{} | done | tools_called={} reply_len={} total_latency={}ms",
            self.name, tools_called, len(reply), total_ms,
        )

        return AgentResult(
            reply=reply,
            tool_calls_made=tools_called,
            structured_data=structured_data,
            agent_name=self.name,
        )
