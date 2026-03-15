"""Meal plan router — AI-powered weekly meal planning via Gemini."""
import time
from dataclasses import replace as dc_replace
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.meal_plan import MealPlan
from app.schemas.meal_plan import MealPlanResponse
from app.services.cache import cache_service
from app.services.llm import llm_provider
from app.services.memory_service import memory_service
from app.services.persona_context import PersonaContextResolver
from app.services.persona_service import persona_service

router = APIRouter(prefix="/mealplan", tags=["Meal Planning"])

VALID_GOALS = {"eat_clean", "weight_loss", "muscle_gain", "keto", "maintenance"}
MAX_USER_NOTE_LEN = 300


class MealPlanRequest(BaseModel):
    goal: str = "eat_clean"
    days: int = Field(default=7, ge=1, le=14)
    calories_target: int = Field(default=2000, ge=1000, le=5000)
    # Persona support
    persona_ids: Optional[List[str]] = Field(
        default=None,
        description="1 hoặc nhiều persona ID để kết hợp phong cách (vd: ['nutrition_expert', 'fitness_coach'])",
    )
    user_note: Optional[str] = Field(
        default=None,
        max_length=MAX_USER_NOTE_LEN,
        description="Mô tả sở thích/ràng buộc cá nhân (dị ứng, kiêng kỵ, thói quen,...). Khi có field này, kết quả sẽ KHÔNG được cache.",
    )


@router.post("/generate")
async def generate_meal_plan(
    request: MealPlanRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Generate an AI meal plan using Gemini 2.5 Flash and save it."""
    if request.goal not in VALID_GOALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"goal must be one of: {', '.join(VALID_GOALS)}",
        )

    logger.info(
        "router:generate_meal_plan | goal={} days={} calories_target={} persona_ids={} has_user_note={}",
        request.goal, request.days, request.calories_target,
        request.persona_ids, bool(request.user_note),
    )
    t0 = time.perf_counter()

    # Resolve persona — multi-persona merge for meal plan
    if request.persona_ids:
        valid_ids = [pid for pid in request.persona_ids if persona_service.exists(pid)]
        if len(valid_ids) > 1:
            # Merge multiple personas into one combined PersonaContext
            persona = PersonaContextResolver.merge_meal_plan_contexts(valid_ids)
        elif len(valid_ids) == 1:
            resolver = PersonaContextResolver(session, cache_service)
            persona = await resolver.resolve(user_id, valid_ids[0])
        else:
            # All provided IDs were invalid — fallback to user's stored setting
            resolver = PersonaContextResolver(session, cache_service)
            persona = await resolver.resolve(user_id, None)
    else:
        resolver = PersonaContextResolver(session, cache_service)
        persona = await resolver.resolve(user_id, None)

    # Inject user memory into meal_plan_prefix
    # Note: when user_note is present, cache is skipped anyway — memory injection
    # is safe to include without busting cache key logic.
    memory_block = await memory_service.get_context_block(user_id, session, cache_service)
    if memory_block:
        persona = dc_replace(
            persona,
            meal_plan_prefix=persona.meal_plan_prefix + "\n\n" + memory_block,
        )

    try:
        ai_result = await llm_provider.generate_meal_plan(
            request.goal, request.days, request.calories_target,
            persona=persona,
            user_note=request.user_note,
        )
    except Exception as e:
        logger.error(
            "router:generate_meal_plan | llm_error={} latency={}ms",
            str(e)[:200], round((time.perf_counter() - t0) * 1000, 1),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )

    # Persist a summary record
    start = date.today()
    end = start + timedelta(days=request.days - 1)
    meal_plan = MealPlan(
        user_id=user_id,
        title=f"Thực đơn {request.days} ngày — {request.goal}",
        description=ai_result.get("nutrition_summary", {}).get("notes", ""),
        start_date=start,
        end_date=end,
        goal=request.goal,
        target_calories=request.calories_target,
    )
    session.add(meal_plan)
    await session.commit()
    await session.refresh(meal_plan)

    plan_days = len(ai_result.get("plan", []))
    nutrition = ai_result.get("nutrition_summary", {})
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    logger.info(
        "router:generate_meal_plan | ok db_id={} plan_days={} avg_calories={} latency={}ms",
        meal_plan.id, plan_days, nutrition.get("avg_calories", "?"), latency_ms,
    )

    return {
        "id": meal_plan.id,
        "goal": request.goal,
        "days": request.days,
        "calories_target": request.calories_target,
        **ai_result,
    }


@router.get("", response_model=List[MealPlanResponse])
async def get_meal_plans(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> List[MealPlanResponse]:
    """List saved meal plans for the current user."""
    logger.debug("db:get_meal_plans | fetching plans")
    t0 = time.perf_counter()
    result = await session.execute(
        select(MealPlan).where(MealPlan.user_id == user_id)
    )
    plans = result.scalars().all()
    logger.info(
        "db:get_meal_plans | count={} latency={}ms",
        len(plans), round((time.perf_counter() - t0) * 1000, 1),
    )
    return [
        MealPlanResponse(
            id=p.id,
            title=p.title,
            description=p.description,
            start_date=p.start_date,
            end_date=p.end_date,
            goal=p.goal,
            target_calories=p.target_calories,
            is_active=p.is_active,
            meal_items=[],
            created_at=p.created_at,
        )
        for p in plans
    ]
