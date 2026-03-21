"""
BaseAgent — abstract base class for all ChefGPT agents.

Each concrete agent declares:
  ALLOWED_TOOLS   — frozenset of tool names it may call
  DEFAULT_PERSONA_ID — which persona JSON to use for its system prompt

The 3-phase agentic loop (plan → execute → synthesize) is implemented
in each subclass's execute() method.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.llm.base_llm import BaseLLM
    from app.services.persona_context import PersonaContext
    from app.services.tool_registry import ToolRegistry


class ToolAccessDeniedError(Exception):
    """Raised when an agent attempts to call a tool not in its ALLOWED_TOOLS."""
    pass


class ToolNotFoundError(Exception):
    pass


@dataclass
class AgentContext:
    """
    Shared context passed to every agent.execute() call.
    Contains all injected dependencies — never derived from LLM output.
    """
    user_id: str
    persona: "PersonaContext"
    history: list[dict]
    db: "AsyncSession"
    memory_block: str = ""          # pre-fetched memory string (inject into system prompt)
    session_id: int | None = None


@dataclass
class AgentResult:
    """
    Structured result returned by agent.execute().
    reply is the human-readable text response.
    structured_data carries domain-specific payloads (e.g. shopping cart).
    """
    reply: str
    tool_calls_made: list[str] = field(default_factory=list)
    structured_data: dict | None = None
    agent_name: str = ""


class BaseAgent(ABC):
    """
    Abstract base for all ChefGPT agents.

    Subclass responsibilities:
      1. Declare ALLOWED_TOOLS and DEFAULT_PERSONA_ID
      2. Implement execute() with the 3-phase loop:
         Phase 1 — Planning:  call LLM to decide which tools to invoke
         Phase 2 — Execution: call each tool via self.call_tool()
         Phase 3 — Synthesis: call LLM again with tool results to generate final answer
    """

    ALLOWED_TOOLS: frozenset[str] = frozenset()
    DEFAULT_PERSONA_ID: str = "asian_chef"

    def __init__(
        self,
        tool_registry: "ToolRegistry",
        llm: "BaseLLM",
    ) -> None:
        self._tools = tool_registry
        self._llm = llm

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    async def execute(self, message: str, context: AgentContext) -> AgentResult:
        """Run one full agent turn. Returns AgentResult."""
        ...

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call an MCP tool by name.

        Enforces ALLOWED_TOOLS whitelist — raises ToolAccessDeniedError if the
        agent is not permitted to use this tool.
        """
        if tool_name not in self.ALLOWED_TOOLS:
            raise ToolAccessDeniedError(
                f"{self.name} is not allowed to call tool '{tool_name}'. "
                f"Allowed: {sorted(self.ALLOWED_TOOLS)}"
            )
        if tool_name not in self._tools:
            raise ToolNotFoundError(
                f"Tool '{tool_name}' is not registered in ToolRegistry."
            )
        logger.debug("{} | call_tool name={} kwargs={}", self.name, tool_name, list(kwargs.keys()))
        return await self._tools.dispatch(tool_name, **kwargs)

    async def call_tools_parallel(
        self, calls: list[tuple[str, dict]]
    ) -> list[Any]:
        """
        Execute multiple tool calls concurrently.
        Each item is (tool_name, kwargs_dict).
        """
        tasks = [self.call_tool(name, **kwargs) for name, kwargs in calls]
        return await asyncio.gather(*tasks, return_exceptions=True)
