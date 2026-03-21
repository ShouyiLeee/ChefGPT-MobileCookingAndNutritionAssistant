"""
AgentRegistry — maps agent name strings to agent instances.

Populated once during app lifespan. Agents are stateless (no per-request state),
so one shared instance per agent type is safe for concurrent async calls.

Usage:
    registry = AgentRegistry(tool_registry, llm_provider)
    chef = registry.get("chef")
    result = await chef.execute(message, context)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from app.agents.chef_agent import ChefAgent
from app.agents.nutritionist_agent import NutritionistAgent
from app.agents.shopping_agent_new import ShoppingAgent

if TYPE_CHECKING:
    from app.agents.base_agent import BaseAgent
    from app.services.llm.base_llm import BaseLLM
    from app.services.tool_registry import ToolRegistry


class AgentRegistry:
    """
    Lazy-initialized registry of agent instances.
    All agents share the same ToolRegistry and LLM provider.
    """

    def __init__(
        self,
        tool_registry: "ToolRegistry",
        llm_provider: "BaseLLM",
    ) -> None:
        self._tools = tool_registry
        self._llm = llm_provider
        self._agents: dict[str, "BaseAgent"] = {}

    def _init_agents(self) -> None:
        """Lazily initialize all agent instances on first access."""
        self._agents = {
            "chef":          ChefAgent(self._tools, self._llm),
            "nutritionist":  NutritionistAgent(self._tools, self._llm),
            "shopping":      ShoppingAgent(self._tools, self._llm),
        }
        logger.info(
            "AgentRegistry | initialized agents: {}",
            list(self._agents.keys()),
        )

    def get(self, name: str) -> "BaseAgent":
        """
        Get an agent instance by name.
        Raises KeyError if the agent name is not registered.
        """
        if not self._agents:
            self._init_agents()
        agent = self._agents.get(name)
        if agent is None:
            raise KeyError(
                f"Agent '{name}' not found. Available: {list(self._agents.keys())}"
            )
        return agent

    def list_agents(self) -> list[str]:
        """Return sorted list of registered agent names."""
        if not self._agents:
            self._init_agents()
        return sorted(self._agents.keys())
