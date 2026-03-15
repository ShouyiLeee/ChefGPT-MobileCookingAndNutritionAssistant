"""
PersonaContext — Dataclass chứa thông tin persona đã được resolve.
PersonaContextResolver — Resolve persona cho mỗi request dựa trên:
  1. persona_id_override từ request body
  2. Redis cache của user setting (TTL 300s)
  3. user_persona_settings table trong DB
  4. Default persona (asian_chef)
"""

import json
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.services.persona_service import persona_service


@dataclass
class PersonaContext:
    persona_id: str
    system_prompt: str
    recipe_prefix: str
    meal_plan_prefix: str
    cuisine_filters: list[str] = field(default_factory=list)


class PersonaContextResolver:
    """
    Resolve PersonaContext theo độ ưu tiên:
    1. persona_id_override (từ request)
    2. Redis cache (TTL 300s)
    3. DB user_persona_settings
    4. Default persona
    """

    CACHE_TTL = 300  # 5 phút

    def __init__(self, db: AsyncSession, cache_service=None) -> None:
        self._db = db
        self._cache = cache_service

    async def resolve(
        self,
        user_id: Optional[str],
        persona_id_override: Optional[str] = None,
    ) -> PersonaContext:
        # 1. Override từ request — check system first, then custom DB
        if persona_id_override:
            if persona_service.exists(persona_id_override):
                return self._build_context(persona_id_override)
            custom = await self._load_custom_persona(persona_id_override)
            if custom:
                return self._build_context_from_raw(custom)

        # 2. Check Redis cache
        if self._cache and user_id:
            cache_key = f"chefgpt:persona_setting:{user_id}"
            cached_id = await self._cache.get_raw(cache_key)
            if cached_id and persona_service.exists(cached_id):
                logger.debug("Persona resolved from cache | user_id={} persona_id={}", user_id, cached_id)
                return self._build_context(cached_id)

        # 3. Query DB
        if user_id:
            try:
                from app.models.user import UserPersonaSetting
                stmt = select(UserPersonaSetting).where(UserPersonaSetting.user_id == user_id)
                result = await self._db.execute(stmt)
                setting = result.scalar_one_or_none()

                if setting:
                    persona_id = setting.active_persona_id
                    if persona_service.exists(persona_id):
                        if self._cache:
                            await self._cache.set_raw(
                                f"chefgpt:persona_setting:{user_id}",
                                persona_id,
                                ttl=self.CACHE_TTL,
                            )
                        return self._build_context(
                            persona_id,
                            custom_overrides_json=setting.custom_prompt_overrides,
                        )
                    # Try custom persona from DB
                    custom = await self._load_custom_persona(persona_id)
                    if custom:
                        if self._cache:
                            await self._cache.set_raw(
                                f"chefgpt:persona_setting:{user_id}",
                                persona_id,
                                ttl=self.CACHE_TTL,
                            )
                        return self._build_context_from_raw(custom)
            except Exception as e:
                logger.warning("Failed to query user persona setting | user_id={} error={}", user_id, e)

        # 4. Fallback: default persona
        default = persona_service.get_default()
        return self._build_context(default["id"])

    async def _load_custom_persona(self, persona_id: str) -> Optional[dict]:
        """Load a custom persona from DB by slug. Returns None if not found."""
        try:
            import json
            from app.models.persona import CustomPersona
            from sqlmodel import select
            result = await self._db.execute(
                select(CustomPersona).where(
                    CustomPersona.slug == persona_id,
                    CustomPersona.is_active == True,
                )
            )
            p = result.scalar_one_or_none()
            if p:
                return {
                    "id": p.slug,
                    "name": p.name,
                    "description": p.description,
                    "icon": p.icon,
                    "color": p.color,
                    "is_default": False,
                    "cuisine_filters": json.loads(p.cuisine_filters or "[]"),
                    "quick_actions": json.loads(p.quick_actions or "[]"),
                    "prompts": {
                        "system": p.system_prompt,
                        "recipe_prefix": p.recipe_prefix,
                        "meal_plan_prefix": p.meal_plan_prefix,
                    },
                }
        except Exception as e:
            logger.warning("Failed to load custom persona | id={} error={}", persona_id, e)
        return None

    def _build_context(
        self,
        persona_id: str,
        custom_overrides_json: Optional[str] = None,
    ) -> PersonaContext:
        config = persona_service.get(persona_id)
        prompts = dict(config.get("prompts", {}))

        # Áp dụng custom overrides nếu có
        if custom_overrides_json:
            try:
                overrides = json.loads(custom_overrides_json)
                for key in ("system", "recipe_prefix", "meal_plan_prefix"):
                    if key in overrides and overrides[key]:
                        prompts[key] = overrides[key]
            except Exception as e:
                logger.warning("Failed to apply persona custom overrides | error={}", e)

        return PersonaContext(
            persona_id=persona_id,
            system_prompt=prompts.get("system", ""),
            recipe_prefix=prompts.get("recipe_prefix", ""),
            meal_plan_prefix=prompts.get("meal_plan_prefix", ""),
            cuisine_filters=config.get("cuisine_filters", []),
        )

    def _build_context_from_raw(self, raw: dict) -> PersonaContext:
        """Build PersonaContext directly from a raw dict (used for custom DB personas)."""
        prompts = raw.get("prompts", {})
        return PersonaContext(
            persona_id=raw["id"],
            system_prompt=prompts.get("system", ""),
            recipe_prefix=prompts.get("recipe_prefix", ""),
            meal_plan_prefix=prompts.get("meal_plan_prefix", ""),
            cuisine_filters=raw.get("cuisine_filters", []),
        )

    @staticmethod
    def merge_meal_plan_contexts(persona_ids: list[str]) -> PersonaContext:
        """
        Merge nhiều personas thành 1 PersonaContext cho meal plan.
        Dùng system prompt của persona đầu tiên, merge tất cả meal_plan_prefixes.
        """
        if not persona_ids:
            default = persona_service.get_default()
            persona_ids = [default["id"]]

        # Validate tất cả
        valid_ids = [pid for pid in persona_ids if persona_service.exists(pid)]
        if not valid_ids:
            default = persona_service.get_default()
            valid_ids = [default["id"]]

        first = persona_service.get(valid_ids[0])
        first_prompts = first.get("prompts", {})

        # Merge meal_plan_prefix từ tất cả personas
        meal_plan_parts = []
        for pid in valid_ids:
            cfg = persona_service.get(pid)
            prefix = cfg.get("prompts", {}).get("meal_plan_prefix", "")
            if prefix:
                meal_plan_parts.append(f"[{cfg['name']}]: {prefix}")

        merged_meal_plan_prefix = "\n".join(meal_plan_parts)

        # Merge cuisine_filters
        all_filters: list[str] = []
        for pid in valid_ids:
            cfg = persona_service.get(pid)
            all_filters.extend(cfg.get("cuisine_filters", []))
        unique_filters = list(dict.fromkeys(all_filters))  # preserve order, deduplicate

        return PersonaContext(
            persona_id="+".join(valid_ids),
            system_prompt=first_prompts.get("system", ""),
            recipe_prefix=first_prompts.get("recipe_prefix", ""),
            meal_plan_prefix=merged_meal_plan_prefix,
            cuisine_filters=unique_filters,
        )
