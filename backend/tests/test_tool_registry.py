"""Unit tests for ToolRegistry."""
import pytest
import pytest_asyncio

from app.services.tool_registry import ToolNotFoundError, ToolRegistry


@pytest.fixture
def registry():
    return ToolRegistry()


@pytest.mark.asyncio
async def test_register_and_dispatch(registry):
    """Registered tool should be callable via dispatch."""
    async def my_tool(x: int) -> int:
        return x * 2

    registry.register("double", my_tool)
    result = await registry.dispatch("double", x=5)
    assert result == 10


@pytest.mark.asyncio
async def test_dispatch_unknown_tool_raises(registry):
    """Dispatching an unregistered tool should raise ToolNotFoundError."""
    with pytest.raises(ToolNotFoundError):
        await registry.dispatch("nonexistent_tool")


def test_list_tools(registry):
    """list_tools() should return sorted names of all registered tools."""
    async def noop(**_): pass

    registry.register("beta_tool", noop)
    registry.register("alpha_tool", noop)
    assert registry.list_tools() == ["alpha_tool", "beta_tool"]


def test_contains(registry):
    """__contains__ should report registered tools correctly."""
    async def noop(**_): pass

    registry.register("my_tool", noop)
    assert "my_tool" in registry
    assert "other_tool" not in registry


@pytest.mark.asyncio
async def test_overwrite_logs_warning(registry, caplog):
    """Re-registering a tool name should overwrite and log a warning."""
    import logging

    async def v1() -> str: return "v1"
    async def v2() -> str: return "v2"

    registry.register("tool", v1)

    with caplog.at_level(logging.WARNING):
        registry.register("tool", v2)

    result = await registry.dispatch("tool")
    assert result == "v2"
