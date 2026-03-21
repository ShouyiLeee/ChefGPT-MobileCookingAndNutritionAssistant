"""Unit tests for CoordinatorAgent — mocks Gemini LLM."""
import json

import pytest

from app.agents.coordinator_agent import CoordinatorAgent, RoutingDecision


class MockLLM:
    """Stub LLM that returns a fixed JSON response."""

    def __init__(self, response: str):
        self._response = response

    async def classify_intent(self, prompt: str) -> str:
        return self._response

    # Required by BaseLLM but not used in these tests
    async def chat(self, *a, **kw): return ""
    async def suggest_recipes(self, *a, **kw): return {}
    async def recognize_ingredients(self, *a, **kw): return {}
    async def generate_meal_plan(self, *a, **kw): return {}
    async def extract_memory_facts(self, *a, **kw): return []


def _make_response(intent: str, primary: str, secondary=None, confidence=0.9) -> str:
    return json.dumps({
        "intent": intent,
        "primary_agent": primary,
        "secondary_agents": secondary or [],
        "confidence": confidence,
    })


@pytest.mark.asyncio
async def test_classify_recipe_intent():
    llm = MockLLM(_make_response("recipe_suggestion", "chef"))
    coordinator = CoordinatorAgent(llm)
    decision = await coordinator.classify("Nấu gì với thịt bò và cà rốt?")
    assert decision.primary_agent == "chef"
    assert decision.intent == "recipe_suggestion"
    assert decision.secondary_agents == []


@pytest.mark.asyncio
async def test_classify_nutrition_intent():
    llm = MockLLM(_make_response("nutrition_analysis", "nutritionist"))
    coordinator = CoordinatorAgent(llm)
    decision = await coordinator.classify("Phở bò có bao nhiêu calories?")
    assert decision.primary_agent == "nutritionist"
    assert decision.intent == "nutrition_analysis"


@pytest.mark.asyncio
async def test_classify_shopping_intent():
    llm = MockLLM(_make_response("shopping_intent", "shopping"))
    coordinator = CoordinatorAgent(llm)
    decision = await coordinator.classify("Mua giúp tôi 1kg thịt bò và rau muống")
    assert decision.primary_agent == "shopping"


@pytest.mark.asyncio
async def test_classify_combined_intent():
    llm = MockLLM(_make_response("combined_recipe_shopping", "chef", ["shopping"]))
    coordinator = CoordinatorAgent(llm)
    decision = await coordinator.classify("Gợi ý món tối và mua nguyên liệu giúp tôi")
    assert decision.primary_agent == "chef"
    assert "shopping" in decision.secondary_agents


@pytest.mark.asyncio
async def test_classify_invalid_json_falls_back_to_chef():
    """If LLM returns invalid JSON, CoordinatorAgent should default to chef."""
    llm = MockLLM("this is not valid json at all")
    coordinator = CoordinatorAgent(llm)
    decision = await coordinator.classify("Anything")
    assert decision.primary_agent == "chef"
    assert decision.confidence == 0.5


@pytest.mark.asyncio
async def test_classify_invalid_agent_name_sanitized():
    """Unknown agent names should be replaced with 'chef'."""
    llm = MockLLM(_make_response("general_chat", "unknown_agent"))
    coordinator = CoordinatorAgent(llm)
    decision = await coordinator.classify("Hello")
    assert decision.primary_agent == "chef"


@pytest.mark.asyncio
async def test_classify_secondary_agent_excluded_if_same_as_primary():
    """Secondary agents list should not contain the primary agent."""
    llm = MockLLM(json.dumps({
        "intent": "combined_recipe_shopping",
        "primary_agent": "chef",
        "secondary_agents": ["chef", "shopping"],  # "chef" is duplicate
        "confidence": 0.9,
    }))
    coordinator = CoordinatorAgent(llm)
    decision = await coordinator.classify("test")
    assert "chef" not in decision.secondary_agents
    assert "shopping" in decision.secondary_agents
