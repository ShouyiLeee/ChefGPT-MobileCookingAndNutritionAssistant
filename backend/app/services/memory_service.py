"""
MemoryService — quản lý bộ nhớ cá nhân của từng user.

Best-practice memory architecture cho LLM assistant:
  1. Automatic extraction: trích xuất facts từ tin nhắn user (background task)
  2. Structured storage: lưu theo (category, key, value) với dedup
  3. Context injection: format thành block text inject vào system_prompt
  4. Redis cache: TTL 10 phút, invalidated khi có memory mới
  5. User control: xem, xóa từng memory, xóa tất cả

Categories:
  dietary    — dị ứng, kiêng kỵ, chế độ ăn đặc biệt
  preference — sở thích ẩm thực, món yêu thích
  aversion   — không thích, tránh
  goal       — mục tiêu dinh dưỡng / sức khỏe
  constraint — hạn chế thời gian, ngân sách, thiết bị
  context    — kỹ năng, số người trong gia đình, v.v.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.memory import UserMemory

if TYPE_CHECKING:
    from app.services.llm.base_llm import BaseLLM

# ── Constants ─────────────────────────────────────────────────────────────────

CACHE_PREFIX = "chefgpt:user_memory:"
CACHE_TTL = 600  # 10 minutes

CATEGORY_CONFIG: dict[str, dict] = {
    "dietary":    {"icon": "🚫", "label": "Chế độ ăn / Dị ứng"},
    "preference": {"icon": "✅", "label": "Sở thích"},
    "aversion":   {"icon": "❌", "label": "Không thích"},
    "goal":       {"icon": "🎯", "label": "Mục tiêu"},
    "constraint": {"icon": "⏰", "label": "Hạn chế"},
    "context":    {"icon": "📝", "label": "Thông tin khác"},
}

VALID_CATEGORIES = set(CATEGORY_CONFIG.keys())
VALID_KEYS = {
    "allergy", "diet_type", "favorite_cuisine", "disliked_ingredient",
    "nutrition_goal", "cooking_time", "household_size", "cooking_skill",
    "budget", "equipment", "other",
}

# ── Extraction prompt ─────────────────────────────────────────────────────────

_EXTRACT_PROMPT = """\
Phân tích tin nhắn dưới đây và extract thông tin cá nhân của user liên quan đến ẩm thực.
Chỉ extract thông tin user NÓI RÕ RÀNG, không suy đoán, không bịa đặt.

Tin nhắn: "{message}"

Trả về JSON array (hoặc [] nếu không có thông tin mới):
[
  {{
    "category": "dietary|preference|aversion|goal|constraint|context",
    "key": "allergy|diet_type|favorite_cuisine|disliked_ingredient|nutrition_goal|cooking_time|household_size|cooking_skill|budget|equipment|other",
    "value": "giá trị cụ thể bằng tiếng Việt, ngắn gọn (≤50 ký tự)"
  }}
]

Ví dụ chuẩn:
- "tôi bị dị ứng tôm" → {{"category":"dietary","key":"allergy","value":"tôm"}}
- "tôi thích món Nhật" → {{"category":"preference","key":"favorite_cuisine","value":"Nhật"}}
- "không ăn được rau mùi" → {{"category":"aversion","key":"disliked_ingredient","value":"rau mùi"}}
- "mục tiêu giảm 5kg" → {{"category":"goal","key":"nutrition_goal","value":"giảm 5kg"}}
- "chỉ có 30 phút nấu" → {{"category":"constraint","key":"cooking_time","value":"30 phút"}}
- "nấu ăn cho gia đình 4 người" → {{"category":"context","key":"household_size","value":"4 người"}}
- "kỹ năng nấu ăn của tôi ở mức trung bình" → {{"category":"context","key":"cooking_skill","value":"trung bình"}}
- "tôi ăn chay" → {{"category":"dietary","key":"diet_type","value":"chay"}}
- "ngân sách nấu ăn khoảng 100k/ngày" → {{"category":"constraint","key":"budget","value":"100k/ngày"}}

Không extract các câu hỏi, yêu cầu gợi ý, hay các câu không phải thông tin cá nhân.
"""


# ── Service ───────────────────────────────────────────────────────────────────

class MemoryService:
    """Singleton service — use the module-level `memory_service` instance."""

    # ── Public: Context injection ──────────────────────────────────────────

    async def get_context_block(
        self,
        user_id: str,
        db: AsyncSession,
        cache=None,
    ) -> str:
        """
        Return a formatted memory block ready to be appended to a system prompt.
        Returns empty string if user has no memories yet.
        Caches result in Redis for CACHE_TTL seconds.
        """
        cache_key = f"{CACHE_PREFIX}{user_id}"

        # 1. Redis cache
        if cache:
            cached = await cache.get_raw(cache_key)
            if cached is not None:
                logger.debug("memory:cache_hit | user_id={}", user_id)
                return cached

        # 2. Load from DB
        memories = await self._load_active(user_id, db)
        if not memories:
            return ""

        context = self._format_context(memories)
        logger.debug(
            "memory:context_built | user_id={} entries={}", user_id, len(memories)
        )

        # 3. Warm cache
        if cache:
            await cache.set_raw(cache_key, context, ttl=CACHE_TTL)

        return context

    # ── Public: Extraction (background task) ──────────────────────────────

    async def extract_and_save(
        self,
        user_id: str,
        user_message: str,
        llm: "BaseLLM",
        db: AsyncSession,
        cache=None,
    ) -> int:
        """
        Extract memory facts from a single user message using LLM, then persist
        them. Deduplication is enforced at DB level (UNIQUE constraint).
        Returns the number of new entries inserted.
        """
        facts = await llm.extract_memory_facts(user_message)
        if not facts:
            return 0

        inserted = 0
        for fact in facts:
            category = fact.get("category", "").strip()
            key = fact.get("key", "").strip()
            value = str(fact.get("value", "")).strip()[:200]

            if not (category and key and value):
                continue
            if category not in VALID_CATEGORIES:
                continue
            if key not in VALID_KEYS:
                key = "other"

            saved = await self._upsert(user_id, category, key, value, db)
            if saved:
                inserted += 1

        if inserted > 0:
            await db.commit()
            # Invalidate cache so next request gets fresh context
            if cache:
                await cache.delete(f"{CACHE_PREFIX}{user_id}")
            logger.info(
                "memory:extracted | user_id={} new_entries={}", user_id, inserted
            )

        return inserted

    # ── Public: CRUD ──────────────────────────────────────────────────────

    async def get_all(self, user_id: str, db: AsyncSession) -> list[UserMemory]:
        """Return all active memories for a user, ordered by category then created_at."""
        result = await db.execute(
            select(UserMemory)
            .where(UserMemory.user_id == user_id, UserMemory.is_active == True)
            .order_by(UserMemory.category, UserMemory.created_at)
        )
        return list(result.scalars().all())

    async def add_explicit(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        db: AsyncSession,
        cache=None,
    ) -> UserMemory:
        """Manually add a memory (source='explicit'). Returns the saved entry."""
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        if key not in VALID_KEYS:
            key = "other"
        value = value.strip()[:200]

        mem = await self._upsert(
            user_id, category, key, value, db, source="explicit"
        )
        if mem is None:
            # Already exists — fetch it
            result = await db.execute(
                select(UserMemory).where(
                    UserMemory.user_id == user_id,
                    UserMemory.category == category,
                    UserMemory.key == key,
                    UserMemory.value == value,
                    UserMemory.is_active == True,
                )
            )
            mem = result.scalar_one()

        await db.commit()
        await db.refresh(mem)

        if cache:
            await cache.delete(f"{CACHE_PREFIX}{user_id}")

        return mem

    async def delete(
        self,
        user_id: str,
        memory_id: int,
        db: AsyncSession,
        cache=None,
    ) -> bool:
        """Soft-delete a single memory. Returns True if found and deleted."""
        result = await db.execute(
            select(UserMemory).where(
                UserMemory.id == memory_id,
                UserMemory.user_id == user_id,
                UserMemory.is_active == True,
            )
        )
        mem = result.scalar_one_or_none()
        if not mem:
            return False

        mem.is_active = False
        mem.updated_at = datetime.utcnow()
        await db.commit()

        if cache:
            await cache.delete(f"{CACHE_PREFIX}{user_id}")

        logger.info("memory:deleted | user_id={} memory_id={}", user_id, memory_id)
        return True

    async def clear_all(
        self,
        user_id: str,
        db: AsyncSession,
        cache=None,
    ) -> int:
        """Soft-delete all memories for a user. Returns count deleted."""
        result = await db.execute(
            select(UserMemory).where(
                UserMemory.user_id == user_id,
                UserMemory.is_active == True,
            )
        )
        memories = list(result.scalars().all())
        now = datetime.utcnow()
        for mem in memories:
            mem.is_active = False
            mem.updated_at = now

        if memories:
            await db.commit()
            if cache:
                await cache.delete(f"{CACHE_PREFIX}{user_id}")

        logger.info(
            "memory:cleared_all | user_id={} count={}", user_id, len(memories)
        )
        return len(memories)

    # ── Private helpers ───────────────────────────────────────────────────

    async def _load_active(
        self, user_id: str, db: AsyncSession
    ) -> list[UserMemory]:
        result = await db.execute(
            select(UserMemory)
            .where(UserMemory.user_id == user_id, UserMemory.is_active == True)
            .order_by(UserMemory.category, UserMemory.created_at)
        )
        return list(result.scalars().all())

    def _format_context(self, memories: list[UserMemory]) -> str:
        """Format memory entries as a structured context block for LLM injection."""
        grouped: dict[str, list[str]] = {}
        for m in memories:
            grouped.setdefault(m.category, []).append(m.value)

        lines = ["[Thông tin đã biết về người dùng này — hãy cá nhân hóa câu trả lời theo đây]"]
        for category, cfg in CATEGORY_CONFIG.items():
            if category in grouped:
                values = ", ".join(grouped[category])
                lines.append(f"{cfg['icon']} {cfg['label']}: {values}")

        return "\n".join(lines)

    async def _upsert(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        db: AsyncSession,
        source: str = "inferred",
    ) -> Optional[UserMemory]:
        """
        Insert a new memory if (user_id, category, key, value) doesn't exist.
        Returns the new entry, or None if it already exists (dedup).
        Does NOT commit — caller must commit.
        """
        # Check for existing active entry
        result = await db.execute(
            select(UserMemory).where(
                UserMemory.user_id == user_id,
                UserMemory.category == category,
                UserMemory.key == key,
                UserMemory.value == value,
                UserMemory.is_active == True,
            )
        )
        if result.scalar_one_or_none():
            return None  # already exists

        mem = UserMemory(
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            source=source,
            confidence=1.0 if source == "explicit" else 0.85,
            created_at=datetime.utcnow(),
        )
        db.add(mem)
        await db.flush()
        return mem


# ── Module singleton ──────────────────────────────────────────────────────────

memory_service = MemoryService()
