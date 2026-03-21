"""
ShoppingAgent — upgrades the existing ShoppingAgentService into a full agent.

This is a NEW agent class. It does NOT replace app/services/shopping_agent.py
(which remains as the singleton service). This agent uses ShoppingMCPServer tools
via the ToolRegistry.

Allowed tools: shopping intent, cart building, grocery optimization, ingredient substitution,
               user preferences, recipe search.
Default persona: home_chef.
"""
from __future__ import annotations

import json
import re
import time

from loguru import logger

from app.agents.base_agent import AgentContext, AgentResult, BaseAgent

_PLAN_PROMPT_TEMPLATE = """\
Bạn là {agent_name} — trợ lý mua sắm và lên danh sách nguyên liệu.
Người dùng hỏi: "{message}"

Thông tin về người dùng:
{memory_block}

Công cụ có sẵn:
{tools_desc}

Quyết định gọi những công cụ nào (tối đa {max_tools}) để hỗ trợ mua sắm tốt nhất.
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

Kết quả từ công cụ mua sắm:
{tool_results}

Hãy trả lời người dùng về việc mua sắm, danh sách nguyên liệu hoặc gợi ý cửa hàng.
Nếu có giỏ hàng, hãy tóm tắt ngắn gọn (không liệt kê hết từng item nếu quá nhiều).
Sử dụng tiếng Việt. Không đề cập đến "công cụ" hay "tool".
"""

_TOOLS_DESCRIPTIONS = {
    "detect_shopping_intent": "Phát hiện ý định mua sắm trong tin nhắn",
    "build_shopping_cart": "Xây dựng giỏ hàng từ danh sách nguyên liệu cần mua",
    "optimize_grocery_list": "Tổng hợp danh sách nguyên liệu từ nhiều món ăn",
    "find_ingredient_substitutes": "Gợi ý nguyên liệu thay thế",
    "get_user_memory_context": "Lấy thông tin ghi nhớ về ngân sách và hạn chế",
    "get_user_preferences": "Lấy danh sách sở thích và ngân sách của người dùng",
    "search_community_recipes": "Tìm công thức để xác định nguyên liệu cần mua",
}


class ShoppingAgent(BaseAgent):
    """
    Shopping and grocery planning specialist.
    Handles: purchase intent detection, cart building, grocery list optimization, ingredient sourcing.
    """

    ALLOWED_TOOLS = frozenset({
        "detect_shopping_intent",
        "build_shopping_cart",
        "optimize_grocery_list",
        "find_ingredient_substitutes",
        "get_user_memory_context",
        "get_user_preferences",
        "search_community_recipes",
    })
    DEFAULT_PERSONA_ID = "home_chef"

    INTENTS = frozenset({
        "shopping_intent",
        "grocery_list",
        "ingredient_sourcing",
        "budget_planning",
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
            logger.warning("{} | planning_error={} — using detect_shopping_intent as default", self.name, str(e)[:100])
            # Default fallback: always try to detect shopping intent
            tool_plan = [{"tool": "detect_shopping_intent", "args": {"message": message}, "reason": "fallback"}]

        logger.debug(
            "{} | plan tools_count={} tools={}",
            self.name, len(tool_plan), [p.get("tool") for p in tool_plan],
        )

        # ── Phase 2: Tool Execution ────────────────────────────────────────────
        tool_results: list[dict] = []
        tools_called: list[str] = []
        structured_data: dict | None = None

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

                # Capture shopping cart as structured data
                if tool_name == "build_shopping_cart" and isinstance(result, dict):
                    structured_data = {"cart": result}

                # Auto-chain: if detect_shopping_intent returned intent, build cart
                if (
                    tool_name == "detect_shopping_intent"
                    and isinstance(result, dict)
                    and result.get("has_intent")
                    and "build_shopping_cart" not in tools_called
                ):
                    items = result.get("items_mentioned", [])
                    if items:
                        try:
                            cart_result = await self.call_tool(
                                "build_shopping_cart",
                                items_mentioned=items,
                                suggested_store=result.get("suggested_store"),
                            )
                            tool_results.append({"tool": "build_shopping_cart", "result": cart_result})
                            tools_called.append("build_shopping_cart")
                            if isinstance(cart_result, dict):
                                structured_data = {"cart": cart_result}
                        except Exception as e2:
                            logger.warning("{} | auto_chain_cart_error={}", self.name, str(e2)[:80])

            except Exception as e:
                logger.warning("{} | tool_error name={} error={}", self.name, tool_name, str(e)[:100])
                tool_results.append({"tool": tool_name, "error": str(e)[:100]})

        # ── Phase 3: Synthesis ─────────────────────────────────────────────────
        system_prompt = context.persona.system_prompt or (
            "Bạn là trợ lý mua sắm thực phẩm thông minh. "
            "Giúp người dùng lên danh sách mua sắm và tìm nguyên liệu. Dùng tiếng Việt."
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
            "{} | done | tools_called={} reply_len={} has_cart={} total_latency={}ms",
            self.name, tools_called, len(reply), bool(structured_data), total_ms,
        )

        return AgentResult(
            reply=reply,
            tool_calls_made=tools_called,
            structured_data=structured_data,
            agent_name=self.name,
        )
