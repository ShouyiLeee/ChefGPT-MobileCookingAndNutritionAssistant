"""Persona API endpoints — system personas (JSON) + custom personas (DB)."""
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.persona import CustomPersona
from app.models.user import UserPersonaSetting
from app.schemas.persona import (
    CreatePersonaRequest,
    PersonaDetailResponse,
    PersonaListItem,
    PersonaPromptsDetail,
    SetPersonaRequest,
    UpdatePersonaRequest,
    UserPersonaSettingResponse,
)
from app.services.cache import cache_service
from app.services.persona_service import persona_service

router = APIRouter(prefix="/personas", tags=["Personas"])

PERSONA_CACHE_TTL = 300  # 5 phút


# ── Helpers ───────────────────────────────────────────────────────────────────

def _system_to_list_item(raw: dict) -> PersonaListItem:
    return PersonaListItem(
        id=raw["id"],
        name=raw["name"],
        description=raw["description"],
        icon=raw["icon"],
        color=raw["color"],
        is_default=raw.get("is_default", False),
        is_system=True,
        created_by=None,
        is_public=True,
        cuisine_filters=raw.get("cuisine_filters", []),
        quick_actions=raw.get("quick_actions", []),
    )


def _custom_to_list_item(p: CustomPersona) -> PersonaListItem:
    return PersonaListItem(
        id=p.slug,
        name=p.name,
        description=p.description,
        icon=p.icon,
        color=p.color,
        is_default=False,
        is_system=False,
        created_by=p.created_by,
        is_public=p.is_public,
        cuisine_filters=json.loads(p.cuisine_filters or "[]"),
        quick_actions=json.loads(p.quick_actions or "[]"),
    )


def _custom_to_detail(p: CustomPersona) -> PersonaDetailResponse:
    item = _custom_to_list_item(p)
    return PersonaDetailResponse(
        **item.model_dump(),
        prompts=PersonaPromptsDetail(
            system=p.system_prompt,
            recipe_prefix=p.recipe_prefix,
            meal_plan_prefix=p.meal_plan_prefix,
        ),
    )


async def _resolve_persona_id(
    persona_id: str,
    session: AsyncSession,
) -> Optional[dict]:
    """Return raw persona dict from system or DB. None if not found."""
    if persona_service.exists(persona_id):
        return persona_service.get(persona_id)
    # Try custom persona by slug
    result = await session.execute(
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
    return None


# ── Public: List & Detail ─────────────────────────────────────────────────────

@router.get("", response_model=list[PersonaListItem])
async def list_personas(
    user_id: Optional[str] = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Trả về danh sách personas:
    - Tất cả system personas (JSON, luôn hiển thị)
    - Custom personas công khai (is_public=True) từ mọi user
    - Custom personas riêng tư của chính user đang login
    """
    items: list[PersonaListItem] = [
        _system_to_list_item(p) for p in persona_service.list_all()
    ]

    # Custom personas: public ones + user's own private ones
    conditions = [CustomPersona.is_public == True, CustomPersona.is_active == True]
    if user_id:
        conditions = [
            CustomPersona.is_active == True,
            or_(
                CustomPersona.is_public == True,
                CustomPersona.created_by == user_id,
            ),
        ]

    result = await session.execute(
        select(CustomPersona)
        .where(*conditions)
        .order_by(CustomPersona.created_at.desc())
    )
    custom = result.scalars().all()
    items.extend(_custom_to_list_item(p) for p in custom)

    return items


@router.get("/me", response_model=UserPersonaSettingResponse)
async def get_my_persona(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Trả về persona đang active của user hiện tại."""
    stmt = select(UserPersonaSetting).where(UserPersonaSetting.user_id == user_id)
    setting = (await session.execute(stmt)).scalar_one_or_none()

    active_id = setting.active_persona_id if setting else persona_service.get_default()["id"]
    has_overrides = bool(setting and setting.custom_prompt_overrides)

    raw = await _resolve_persona_id(active_id, session)
    if not raw:
        raw = persona_service.get_default()
        active_id = raw["id"]

    return UserPersonaSettingResponse(
        active_persona_id=active_id,
        persona=PersonaListItem(
            id=raw["id"],
            name=raw["name"],
            description=raw["description"],
            icon=raw["icon"],
            color=raw["color"],
            is_default=raw.get("is_default", False),
            is_system=persona_service.exists(raw["id"]),
            cuisine_filters=raw.get("cuisine_filters", []),
            quick_actions=raw.get("quick_actions", []),
        ),
        has_custom_overrides=has_overrides,
    )


@router.get("/{persona_id}", response_model=PersonaDetailResponse)
async def get_persona(
    persona_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Trả về chi tiết 1 persona.
    Prompts chỉ được trả về nếu đây là custom persona của chính user.
    """
    # System persona
    if persona_service.exists(persona_id):
        raw = persona_service.get(persona_id)
        return PersonaDetailResponse(
            id=raw["id"],
            name=raw["name"],
            description=raw["description"],
            icon=raw["icon"],
            color=raw["color"],
            is_default=raw.get("is_default", False),
            is_system=True,
            is_public=True,
            cuisine_filters=raw.get("cuisine_filters", []),
            quick_actions=raw.get("quick_actions", []),
            prompts=None,  # system prompts are server-side only
        )

    # Custom persona
    result = await session.execute(
        select(CustomPersona).where(
            CustomPersona.slug == persona_id,
            CustomPersona.is_active == True,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    # Visibility check
    if not p.is_public and p.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    detail = _custom_to_detail(p)
    # Only return prompts to the owner
    if p.created_by != user_id:
        detail.prompts = None
    return detail


# ── User setting (active persona) ─────────────────────────────────────────────
# IMPORTANT: /me and /me/overrides must be declared BEFORE /{persona_id}
# to prevent FastAPI treating "me" as a persona_id path parameter.

@router.put("/me", response_model=UserPersonaSettingResponse)
async def set_my_persona(
    body: SetPersonaRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Đặt active persona cho user. Chấp nhận cả system và custom persona IDs."""
    raw = await _resolve_persona_id(body.persona_id, session)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found",
        )

    # Validate custom_overrides keys
    allowed_override_keys = {"system", "recipe_prefix", "meal_plan_prefix"}
    overrides_json: str | None = None
    if body.custom_overrides:
        invalid_keys = set(body.custom_overrides.keys()) - allowed_override_keys
        if invalid_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid override keys: {invalid_keys}. Allowed: {allowed_override_keys}",
            )
        overrides_json = json.dumps(body.custom_overrides, ensure_ascii=False)

    # Upsert setting
    stmt = select(UserPersonaSetting).where(UserPersonaSetting.user_id == user_id)
    setting = (await session.execute(stmt)).scalar_one_or_none()

    if setting:
        setting.active_persona_id = body.persona_id
        setting.custom_prompt_overrides = overrides_json
        setting.updated_at = datetime.utcnow()
    else:
        setting = UserPersonaSetting(
            user_id=user_id,
            active_persona_id=body.persona_id,
            custom_prompt_overrides=overrides_json,
        )
        session.add(setting)

    await session.commit()

    # Invalidate + warm Redis cache
    cache_key = f"chefgpt:persona_setting:{user_id}"
    await cache_service.delete(cache_key)
    await cache_service.set_raw(cache_key, body.persona_id, ttl=PERSONA_CACHE_TTL)

    logger.info("persona:set_active | user_id={} persona_id={}", user_id, body.persona_id)
    return UserPersonaSettingResponse(
        active_persona_id=body.persona_id,
        persona=PersonaListItem(
            id=raw["id"],
            name=raw["name"],
            description=raw["description"],
            icon=raw["icon"],
            color=raw["color"],
            is_default=raw.get("is_default", False),
            is_system=persona_service.exists(raw["id"]),
            cuisine_filters=raw.get("cuisine_filters", []),
            quick_actions=raw.get("quick_actions", []),
        ),
        has_custom_overrides=overrides_json is not None,
    )


@router.delete("/me/overrides", status_code=status.HTTP_204_NO_CONTENT)
async def reset_my_overrides(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Reset custom overrides về platform default."""
    stmt = select(UserPersonaSetting).where(UserPersonaSetting.user_id == user_id)
    setting = (await session.execute(stmt)).scalar_one_or_none()
    if setting and setting.custom_prompt_overrides:
        setting.custom_prompt_overrides = None
        setting.updated_at = datetime.utcnow()
        await session.commit()
        logger.info("persona:reset_overrides | user_id={}", user_id)


# ── Custom Persona CRUD ───────────────────────────────────────────────────────

@router.post("", response_model=PersonaDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    body: CreatePersonaRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Tạo custom persona mới.
    Slug được tự động tạo từ tên + uuid ngắn.
    """
    # Generate unique slug
    name_slug = "".join(
        c if c.isalnum() else "_" for c in body.name.lower()
    ).strip("_")[:20]
    slug = f"custom_{name_slug}_{uuid.uuid4().hex[:6]}"

    persona = CustomPersona(
        slug=slug,
        created_by=user_id,
        name=body.name,
        description=body.description,
        icon=body.icon,
        color=body.color,
        system_prompt=body.system_prompt,
        recipe_prefix=body.recipe_prefix,
        meal_plan_prefix=body.meal_plan_prefix,
        cuisine_filters=json.dumps(body.cuisine_filters, ensure_ascii=False),
        quick_actions=json.dumps(body.quick_actions, ensure_ascii=False),
        is_public=body.is_public,
        created_at=datetime.utcnow(),
    )
    session.add(persona)
    await session.commit()
    await session.refresh(persona)

    logger.info(
        "persona:create | user_id={} slug={} name={} is_public={}",
        user_id, slug, body.name, body.is_public,
    )
    return _custom_to_detail(persona)


@router.put("/{persona_id}", response_model=PersonaDetailResponse)
async def update_persona(
    persona_id: str,
    body: UpdatePersonaRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Cập nhật custom persona. Chỉ owner mới có thể sửa."""
    if persona_service.exists(persona_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System personas cannot be modified. Create a custom persona instead.",
        )

    result = await session.execute(
        select(CustomPersona).where(
            CustomPersona.slug == persona_id,
            CustomPersona.is_active == True,
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    if persona.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your persona")

    if body.name is not None:
        persona.name = body.name
    if body.description is not None:
        persona.description = body.description
    if body.icon is not None:
        persona.icon = body.icon
    if body.color is not None:
        persona.color = body.color
    if body.system_prompt is not None:
        persona.system_prompt = body.system_prompt
    if body.recipe_prefix is not None:
        persona.recipe_prefix = body.recipe_prefix
    if body.meal_plan_prefix is not None:
        persona.meal_plan_prefix = body.meal_plan_prefix
    if body.cuisine_filters is not None:
        persona.cuisine_filters = json.dumps(body.cuisine_filters, ensure_ascii=False)
    if body.quick_actions is not None:
        persona.quick_actions = json.dumps(body.quick_actions, ensure_ascii=False)
    if body.is_public is not None:
        persona.is_public = body.is_public
    persona.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(persona)

    logger.info("persona:update | user_id={} slug={}", user_id, persona_id)
    return _custom_to_detail(persona)


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: str,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Xóa (soft-delete) custom persona. Chỉ owner mới có thể xóa."""
    if persona_service.exists(persona_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System personas cannot be deleted.",
        )

    result = await session.execute(
        select(CustomPersona).where(
            CustomPersona.slug == persona_id,
            CustomPersona.is_active == True,
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    if persona.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your persona")

    persona.is_active = False
    persona.updated_at = datetime.utcnow()
    await session.commit()

    logger.info("persona:delete | user_id={} slug={}", user_id, persona_id)

