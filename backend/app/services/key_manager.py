"""Gemini API key manager with round-robin rotation and rate-limit cooldown."""
import hashlib

from loguru import logger

from app.services.cache import CacheService


class GeminiKeyManager:
    """
    Rotates through a pool of Gemini API keys using Redis-backed round-robin.
    Keys that receive a 429 / RESOURCE_EXHAUSTED response are put in cooldown
    and skipped until the cooldown expires.
    """

    _COUNTER_KEY = "chefgpt:key_index"
    _COOLDOWN_PREFIX = "chefgpt:ratelimit:"
    DEFAULT_COOLDOWN = 60  # seconds

    def __init__(self, api_keys: list[str], cache: CacheService) -> None:
        self._keys = api_keys
        self._cache = cache

    async def get_key(self) -> str:
        """Return the next available (non-rate-limited) API key."""
        if not self._keys:
            raise RuntimeError("No Gemini API keys configured — set GEMINI_API_KEY or GEMINI_API_KEYS")

        for _ in range(len(self._keys)):
            index = await self._cache.incr(self._COUNTER_KEY)
            key = self._keys[(index - 1) % len(self._keys)]
            if not await self._is_rate_limited(key):
                return key

        # All keys are in cooldown — fall back to first key and log an error
        logger.error("All {} Gemini API keys are rate-limited, using first key anyway", len(self._keys))
        return self._keys[0]

    async def mark_rate_limited(self, key: str, cooldown: int = DEFAULT_COOLDOWN) -> None:
        """Mark a key as rate-limited for `cooldown` seconds."""
        rate_key = self._cooldown_key(key)
        await self._cache.set_ex(rate_key, "1", cooldown)
        logger.warning(
            "Gemini key ...{} rate-limited — cooldown {}s", key[-6:], cooldown
        )

    async def _is_rate_limited(self, key: str) -> bool:
        return await self._cache.exists(self._cooldown_key(key))

    @staticmethod
    def _cooldown_key(key: str) -> str:
        return GeminiKeyManager._COOLDOWN_PREFIX + hashlib.sha256(key.encode()).hexdigest()[:16]
