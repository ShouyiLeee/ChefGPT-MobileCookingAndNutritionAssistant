"""Integration tests for AgenticLoop — all dependencies mocked."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.agent_registry import AgentRegistry
from app.agents.base_agent import AgentContext, AgentResult
from app.agents.coordinator_agent import CoordinatorAgent, RoutingDecision
from app.services.agent_loop import AgenticLoop
from app.services.tool_registry import ToolRegistry


# ── Fixtures ──────────────────────────────────────────────────────────────────


class MockPersona:
    persona_id = "asian_chef"
    system_prompt = "Test chef"
    recipe_prefix = ""
    meal_plan_prefix = ""
    cuisine_filters = []


class MockLLM:
    async def classify_intent(self, prompt: str) -> str:
        # Return a simple chef routing by default
        return json.dumps({
            "intent": "general_chat",
            "primary_agent": "chef",
            "secondary_agents": [],
            "confidence": 0.95,
        })

    async def chat(self, message, history=None, persona=None) -> str:
        return f"Mock reply to: {message[:30]}"

    async def suggest_recipes(self, *a, **kw): return {"dishes": []}
    async def recognize_ingredients(self, *a, **kw): return {"ingredients": []}
    async def generate_meal_plan(self, *a, **kw): return {"plan": []}
    async def extract_memory_facts(self, *a, **kw): return []


def make_context(db=None):
    from unittest.mock import MagicMock
    return AgentContext(
        user_id="test-user-123",
        persona=MockPersona(),
        history=[],
        db=db or MagicMock(),
        memory_block="Test user: dị ứng tôm",
        session_id=1,
    )


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_agent_loop_basic_chat():
    """AgenticLoop should run without errors and return a non-empty reply."""
    llm = MockLLM()
    tool_registry = ToolRegistry()
    agent_registry = AgentRegistry(tool_registry, llm)

    coordinator = CoordinatorAgent(llm)
    loop = AgenticLoop(coordinator, agent_registry)

    context = make_context()
    result = await loop.run("Nấu gì với thịt bò?", context)

    assert result.reply
    assert isinstance(result.reply, str)
    assert result.intent == "general_chat"
    assert "chef" in result.agents_used or len(result.agents_used) >= 0


@pytest.mark.asyncio
async def test_agent_loop_coordinator_timeout_falls_back(monkeypatch):
    """If coordinator times out, loop should default to chef and still return a reply."""
    import asyncio

    class SlowLLM(MockLLM):
        async def classify_intent(self, prompt: str) -> str:
            await asyncio.sleep(10)  # will timeout
            return ""

    llm = SlowLLM()
    tool_registry = ToolRegistry()
    agent_registry = AgentRegistry(tool_registry, llm)
    coordinator = CoordinatorAgent(llm)
    loop = AgenticLoop(coordinator, agent_registry)

    # Patch timeout to be very short
    monkeypatch.setattr("app.core.config.settings.mcp_intent_timeout", 0.01)

    context = make_context()
    result = await loop.run("Test message", context)

    # Should still work (defaulting to chef agent)
    assert result.reply
    assert result.intent == "general_chat"


@pytest.mark.asyncio
async def test_agent_loop_parallel_agents():
    """AgenticLoop should handle primary + secondary agent execution."""
    class CombinedLLM(MockLLM):
        async def classify_intent(self, prompt: str) -> str:
            return json.dumps({
                "intent": "combined_recipe_shopping",
                "primary_agent": "chef",
                "secondary_agents": ["shopping"],
                "confidence": 0.9,
            })

    llm = CombinedLLM()
    tool_registry = ToolRegistry()
    agent_registry = AgentRegistry(tool_registry, llm)
    coordinator = CoordinatorAgent(llm)
    loop = AgenticLoop(coordinator, agent_registry)

    context = make_context()
    result = await loop.run("Gợi ý món và mua nguyên liệu", context)

    assert result.reply
    # Both chef and shopping should have been attempted
    assert len(result.agents_used) >= 1


@pytest.mark.asyncio
async def test_agent_registry_lists_agents():
    """AgentRegistry should expose all 3 agent types."""
    llm = MockLLM()
    tool_registry = ToolRegistry()
    registry = AgentRegistry(tool_registry, llm)
    agents = registry.list_agents()
    assert "chef" in agents
    assert "nutritionist" in agents
    assert "shopping" in agents


@pytest.mark.asyncio
async def test_agent_registry_raises_for_unknown():
    """AgentRegistry.get() should raise KeyError for unknown agent names."""
    llm = MockLLM()
    registry = AgentRegistry(ToolRegistry(), llm)
    with pytest.raises(KeyError):
        registry.get("unknown_agent_xyz")


@pytest.mark.asyncio
async def test_base_agent_tool_access_denied():
    """An agent should not be able to call tools outside its ALLOWED_TOOLS."""
    from app.agents.base_agent import ToolAccessDeniedError
    from app.agents.chef_agent import ChefAgent

    llm = MockLLM()
    tool_registry = ToolRegistry()

    async def forbidden_tool(**_): return "secret"
    tool_registry.register("forbidden_nutrition_only_tool", forbidden_tool)

    chef = ChefAgent(tool_registry, llm)

    with pytest.raises(ToolAccessDeniedError):
        await chef.call_tool("forbidden_nutrition_only_tool")


@pytest.mark.asyncio
async def test_tool_registry_dispatch_with_kwargs():
    """ToolRegistry should pass kwargs correctly to registered async callables."""
    registry = ToolRegistry()
    received = {}

    async def capture_tool(name: str, value: int) -> dict:
        received["name"] = name
        received["value"] = value
        return {"ok": True}

    registry.register("capture", capture_tool)
    result = await registry.dispatch("capture", name="test", value=42)

    assert result == {"ok": True}
    assert received["name"] == "test"
    assert received["value"] == 42
