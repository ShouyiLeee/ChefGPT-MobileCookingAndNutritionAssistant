"""Redis cache service for ChefGPT."""
import hashlib
import json
from typing import Optional

import redis.asyncio as aioredis
from loguru import logger

from app.core.config import settings


class CacheService:
    """Async Redis wrapper with graceful fallback when Redis is unavailable."""

    def __init__(self, redis_url: str) -> None:
        self._url = redis_url
        self._redis: Optional[aioredis.Redis] = None

    async def _client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._url, decode_responses=True)
        return self._redis

    async def get(self, key: str) -> Optional[dict | list]:
        try:
            r = await self._client()
            data = await r.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning("Cache get failed key={}: {}", key, e)
        return None

    async def set(self, key: str, value: dict | list, ttl: int) -> None:
        try:
            r = await self._client()
            await r.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        except Exception as e:
            logger.warning("Cache set failed key={}: {}", key, e)

    async def incr(self, key: str) -> int:
        """Atomically increment a counter (used for round-robin key selection)."""
        try:
            r = await self._client()
            return await r.incr(key)
        except Exception as e:
            logger.warning("Cache incr failed key={}: {}", key, e)
            return 1

    async def set_ex(self, key: str, value: str, ttl: int) -> None:
        """Set a string value with expiry (used for rate-limit cooldown markers)."""
        try:
            r = await self._client()
            await r.set(key, value, ex=ttl)
        except Exception as e:
            logger.warning("Cache set_ex failed key={}: {}", key, e)

    async def exists(self, key: str) -> bool:
        try:
            r = await self._client()
            return bool(await r.exists(key))
        except Exception:
            return False

    async def get_raw(self, key: str) -> Optional[str]:
        """Get a raw string value (e.g. persona_id)."""
        try:
            r = await self._client()
            return await r.get(key)
        except Exception as e:
            logger.warning("Cache get_raw failed key={}: {}", key, e)
        return None

    async def set_raw(self, key: str, value: str, ttl: int) -> None:
        """Set a raw string value with TTL."""
        try:
            r = await self._client()
            await r.set(key, value, ex=ttl)
        except Exception as e:
            logger.warning("Cache set_raw failed key={}: {}", key, e)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        try:
            r = await self._client()
            await r.delete(key)
        except Exception as e:
            logger.warning("Cache delete failed key={}: {}", key, e)

    async def ping(self) -> bool:
        try:
            r = await self._client()
            return bool(await r.ping())
        except Exception:
            return False

    @staticmethod
    def make_key(prefix: str, **params) -> str:
        """Build a deterministic cache key from a prefix + arbitrary kwargs."""
        payload = json.dumps(params, sort_keys=True, ensure_ascii=False)
        hash_hex = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return f"chefgpt:{prefix}:{hash_hex}"


# Singleton — shared across all requests
cache_service = CacheService(settings.redis_url)
