"""
ToolRegistry — central registry mapping tool_name → async callable.

MCP servers call register_tools(registry) during app lifespan to populate this.
Agents call dispatch(tool_name, **kwargs) to invoke tools by name.

Design:
  - Lightweight: plain dict, no serialization/transport overhead in-process
  - FastMCP provides schema/documentation; ToolRegistry provides runtime dispatch
  - thread-safe for asyncio (single-thread event loop)
"""
from __future__ import annotations

from typing import Any, Callable

from loguru import logger


class ToolNotFoundError(Exception):
    pass


class ToolAccessDeniedError(Exception):
    pass


class ToolRegistry:
    """
    Central registry of all MCP tools available to agents.
    Populated at startup by each MCP server calling register_tools(self).
    """

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}

    def register(self, tool_name: str, fn: Callable) -> None:
        """Register an async callable under a tool name."""
        if tool_name in self._tools:
            logger.warning("tool_registry | overwriting existing tool name={}", tool_name)
        self._tools[tool_name] = fn
        logger.debug("tool_registry | registered tool={}", tool_name)

    async def dispatch(self, tool_name: str, **kwargs) -> Any:
        """
        Look up and call a tool by name.
        Raises ToolNotFoundError if no such tool is registered.
        """
        fn = self._tools.get(tool_name)
        if fn is None:
            raise ToolNotFoundError(f"Tool '{tool_name}' is not registered. Available: {self.list_tools()}")
        logger.debug("tool_registry | dispatch tool={} kwargs_keys={}", tool_name, list(kwargs.keys()))
        return await fn(**kwargs)

    def list_tools(self) -> list[str]:
        """Return sorted list of all registered tool names."""
        return sorted(self._tools.keys())

    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools


# Module-level singleton — initialized empty, populated in app lifespan
tool_registry = ToolRegistry()
