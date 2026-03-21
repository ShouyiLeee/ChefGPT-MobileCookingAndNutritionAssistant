"""
AgenticLoop — orchestrates the full multi-agent pipeline for a single chat turn.

Flow:
  1. CoordinatorAgent.classify() → RoutingDecision (primary + optional secondaries)
  2. Resolve agent instances from AgentRegistry
  3. Execute primary agent (always)
  4. Execute secondary agents in parallel if any
  5. Merge results → AgentLoopResult

The AgentLoopResult is shaped to match ChatMessageResponse exactly:
  - reply          → ChatMessageResponse.message
  - shopping_data  → ChatMessageResponse.shopping_suggestion

This ensures the Flutter app receives identical schema whether MCP is enabled or not.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.agents.agent_registry import AgentRegistry
    from app.agents.base_agent import AgentContext
    from app.agents.coordinator_agent import CoordinatorAgent


@dataclass
class AgentLoopResult:
    """
    Final output of one agentic loop turn.
    Maps directly onto ChatMessageResponse fields.
    """
    reply: str
    shopping_suggestion: dict | None = None   # maps to ChatMessageResponse.shopping_suggestion
    agents_used: list[str] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    intent: str = "general_chat"


class AgenticLoop:
    """
    Orchestrates intent classification, agent dispatch, and result merging.

    One shared instance per app (stateless — safe for concurrent requests).
    """

    def __init__(
        self,
        coordinator: "CoordinatorAgent",
        agent_registry: "AgentRegistry",
    ) -> None:
        self._coordinator = coordinator
        self._registry = agent_registry

    async def run(
        self,
        message: str,
        context: "AgentContext",
    ) -> AgentLoopResult:
        """
        Execute a full agentic turn for a user message.

        Args:
            message: The user's input text
            context: AgentContext with user_id, persona, history, db, memory_block

        Returns:
            AgentLoopResult ready to be mapped onto ChatMessageResponse
        """
        from app.core.config import settings

        t0 = time.perf_counter()
        logger.info(
            "agent_loop | start | user_id={} message_len={} persona={}",
            context.user_id, len(message), context.persona.persona_id,
        )

        # ── Step 1: Intent classification ──────────────────────────────────────
        try:
            decision = await asyncio.wait_for(
                self._coordinator.classify(
                    message,
                    history=context.history,
                    memory_block=context.memory_block,
                ),
                timeout=settings.mcp_intent_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "agent_loop | coordinator_timeout after {}s — defaulting to chef",
                settings.mcp_intent_timeout,
            )
            from app.agents.coordinator_agent import RoutingDecision
            decision = RoutingDecision(primary_agent="chef", intent="general_chat", confidence=0.5)
        except Exception as e:
            logger.warning("agent_loop | coordinator_error={} — defaulting to chef", str(e)[:100])
            from app.agents.coordinator_agent import RoutingDecision
            decision = RoutingDecision(primary_agent="chef", intent="general_chat", confidence=0.5)

        logger.info(
            "agent_loop | routed intent={} primary={} secondary={}",
            decision.intent, decision.primary_agent, decision.secondary_agents,
        )

        # ── Step 2: Resolve agents ──────────────────────────────────────────────
        try:
            primary_agent = self._registry.get(decision.primary_agent)
        except KeyError:
            logger.warning("agent_loop | unknown primary_agent={} — falling back to chef", decision.primary_agent)
            primary_agent = self._registry.get("chef")

        secondary_agents = []
        for name in decision.secondary_agents:
            try:
                secondary_agents.append(self._registry.get(name))
            except KeyError:
                logger.warning("agent_loop | unknown secondary_agent={} — skipping", name)

        # ── Steps 3 & 4: Execute primary + secondaries in parallel ─────────────
        all_tasks = [primary_agent.execute(message, context)]
        for agent in secondary_agents:
            all_tasks.append(agent.execute(message, context))

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*all_tasks, return_exceptions=True),
                timeout=settings.mcp_tool_timeout * settings.mcp_max_tool_iterations,
            )
        except asyncio.TimeoutError:
            logger.error("agent_loop | execution_timeout — falling back to primary only")
            # Fallback: run primary with no tools
            results = [await primary_agent.execute(message, context)]

        # ── Step 5: Merge results ───────────────────────────────────────────────
        primary_result = None
        shopping_suggestion: dict | None = None
        all_tool_calls: list[str] = []
        agents_used: list[str] = []

        for result in results:
            if isinstance(result, Exception):
                logger.error("agent_loop | agent_exception={}", str(result)[:200])
                continue

            agents_used.append(result.agent_name)
            all_tool_calls.extend(result.tool_calls_made)

            # Primary agent provides the reply text
            if result.agent_name == primary_agent.name:
                primary_result = result

            # Any agent can contribute structured data (shopping cart wins)
            if result.structured_data and "cart" in result.structured_data:
                shopping_suggestion = result.structured_data["cart"]

        # Fallback if primary failed
        if primary_result is None:
            logger.error("agent_loop | primary_agent_failed — returning error message")
            return AgentLoopResult(
                reply="Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu của bạn. Vui lòng thử lại.",
                shopping_suggestion=None,
                agents_used=agents_used,
                tool_calls=all_tool_calls,
                intent=decision.intent,
            )

        # Build shopping_suggestion in the format expected by ChatMessageResponse
        final_shopping = None
        if shopping_suggestion:
            # Wrap cart dict in ShoppingSuggestion shape if needed
            # (AgentLoopResult.shopping_suggestion is passed directly as
            # ChatMessageResponse.shopping_suggestion which accepts any dict)
            final_shopping = _build_shopping_suggestion(shopping_suggestion)

        total_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(
            "agent_loop | done | intent={} agents_used={} tools_called={} has_cart={} latency={}ms",
            decision.intent, agents_used, all_tool_calls, bool(final_shopping), total_ms,
        )

        return AgentLoopResult(
            reply=primary_result.reply,
            shopping_suggestion=final_shopping,
            agents_used=agents_used,
            tool_calls=all_tool_calls,
            intent=decision.intent,
        )


def _build_shopping_suggestion(cart: dict) -> dict:
    """
    Wrap a raw cart dict into the ShoppingSuggestionSchema-compatible shape
    expected by ChatMessageResponse.shopping_suggestion.

    This preserves backward compatibility with the Flutter app.
    """
    from app.schemas.order import (
        CartMandateSchema,
        CartMandateItemSchema,
        ShoppingSuggestionSchema,
    )

    try:
        items = [
            CartMandateItemSchema(
                product_id=i.get("product_id", ""),
                product_name=i.get("product_name", ""),
                product_emoji=i.get("product_emoji", "🛒"),
                unit=i.get("unit", "gói"),
                quantity=i.get("quantity", 1),
                unit_price=i.get("unit_price", 0.0),
                subtotal=i.get("subtotal", 0.0),
            )
            for i in cart.get("items", [])
        ]
        cart_schema = CartMandateSchema(
            store_id=cart.get("store_id", ""),
            store_name=cart.get("store_name", ""),
            items=items,
            subtotal=cart.get("subtotal", 0.0),
            delivery_fee=cart.get("delivery_fee", 0.0),
            estimated_total=cart.get("estimated_total", 0.0),
            intent_description=cart.get("intent_description", ""),
        )
        suggestion = ShoppingSuggestionSchema(
            cart_mandate=cart_schema,
            estimated_total=cart.get("estimated_total", 0.0),
            requires_confirmation=True,
            mandate_id=None,
        )
        return suggestion.model_dump()
    except Exception as e:
        logger.warning("agent_loop | shopping_suggestion_build_error={}", str(e)[:100])
        # Return raw cart as fallback
        return cart
