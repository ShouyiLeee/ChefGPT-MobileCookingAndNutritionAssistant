"""
MemoryMCPServer — tools for user memory retrieval and management.

SECURITY: user_id is always injected by the agent from request context.
It is NEVER derived from LLM output to prevent prompt-injection attacks.

Tools:
  get_user_memory_context   — formatted memory block for system prompt injection
  get_user_preferences      — structured preference list, optionally filtered by category
  extract_and_save_facts    — background memory extraction (called via BackgroundTasks)
  add_user_preference       — explicitly add a preference (from confirmed user input)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.services.cache import CacheService
    from app.services.memory_service import MemoryService
    from app.services.tool_registry import ToolRegistry


class MemoryMCPServer:
    """MCP server wrapping user memory operations."""

    def __init__(
        self,
        memory_service: "MemoryService",
        cache_service: "CacheService",
    ) -> None:
        self._memory = memory_service
        self._cache = cache_service

    def register_tools(self, registry: "ToolRegistry") -> None:
        registry.register("get_user_memory_context", self.get_user_memory_context)
        registry.register("get_user_preferences", self.get_user_preferences)
        registry.register("extract_and_save_facts", self.extract_and_save_facts)
        registry.register("add_user_preference", self.add_user_preference)
        logger.info("MemoryMCPServer | registered 4 tools")

    # ── Tools ──────────────────────────────────────────────────────────────────

    async def get_user_memory_context(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> str:
        """
        Return the user's memory as a formatted block for system prompt injection.
        Uses Redis cache (TTL 10 min). Returns empty string if no memories found.

        Args:
            user_id: Authenticated user ID (injected by agent — never from LLM)
            db: AsyncSession (injected by agent)

        Returns:
            Formatted memory block string (e.g. "🚫 Dị ứng: tôm\\n✅ Sở thích: ẩm thực Á Đông")
        """
        logger.debug("tool:get_user_memory_context | user_id={}", user_id)
        block = await self._memory.get_context_block(user_id, db, self._cache)
        return block or ""

    async def get_user_preferences(
        self,
        user_id: str,
        db: AsyncSession,
        category: str | None = None,
    ) -> list[dict]:
        """
        Get the user's structured memory/preferences, optionally filtered by category.

        Args:
            user_id: Authenticated user ID (injected by agent)
            db: AsyncSession (injected by agent)
            category: Optional filter — one of: dietary, preference, aversion, goal, constraint, context

        Returns:
            List of {id, category, key, value, confidence} dicts
        """
        from app.models.memory import UserMemory
        from sqlmodel import select

        logger.debug("tool:get_user_preferences | user_id={} category={}", user_id, category)

        stmt = select(UserMemory).where(
            UserMemory.user_id == user_id,
            UserMemory.is_active == True,
        )
        if category:
            stmt = stmt.where(UserMemory.category == category)

        result = await db.execute(stmt)
        memories = result.scalars().all()

        return [
            {
                "id": m.id,
                "category": m.category,
                "key": m.key,
                "value": m.value,
                "confidence": m.confidence,
            }
            for m in memories
        ]

    async def extract_and_save_facts(
        self,
        user_id: str,
        message: str,
        db: AsyncSession,
    ) -> dict:
        """
        Extract personal food facts from a user message and persist them.
        This tool is called as a background task — it never blocks the chat response.

        Args:
            user_id: Authenticated user ID (injected by agent)
            message: The user's chat message to analyze
            db: AsyncSession (injected by agent)

        Returns:
            {extracted_count: int}
        """
        from app.services.llm import llm_provider

        logger.debug("tool:extract_and_save_facts | user_id={} message_len={}", user_id, len(message))
        try:
            await self._memory.extract_and_save(user_id, message, llm_provider, db, self._cache)
            return {"extracted_count": 1}
        except Exception as e:
            logger.warning("tool:extract_and_save_facts | error={}", str(e)[:100])
            return {"extracted_count": 0}

    async def add_user_preference(
        self,
        user_id: str,
        db: AsyncSession,
        category: str,
        key: str,
        value: str,
    ) -> dict:
        """
        Explicitly add a user preference (from confirmed user input, not inferred).

        Args:
            user_id: Authenticated user ID (injected by agent)
            db: AsyncSession (injected by agent)
            category: One of: dietary, preference, aversion, goal, constraint, context
            key: Preference key (e.g. "allergy", "favorite_cuisine")
            value: Preference value (e.g. "tôm", "Việt Nam")

        Returns:
            {id, category, key, value}
        """
        from app.models.memory import UserMemory
        from app.services.memory_service import VALID_CATEGORIES, VALID_KEYS

        if category not in VALID_CATEGORIES:
            return {"error": f"Invalid category '{category}'. Valid: {sorted(VALID_CATEGORIES)}"}
        if key not in VALID_KEYS:
            key = "other"

        memory = UserMemory(
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            confidence=1.0,
            source="explicit",
            is_active=True,
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)

        # Invalidate memory cache for this user
        cache_key = f"chefgpt:user_memory:{user_id}"
        await self._cache.delete(cache_key)

        logger.info(
            "tool:add_user_preference | user_id={} category={} key={} value={}",
            user_id, category, key, value,
        )
        return {"id": memory.id, "category": memory.category, "key": memory.key, "value": memory.value}
