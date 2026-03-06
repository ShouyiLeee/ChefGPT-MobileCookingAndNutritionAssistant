"""Meal plan router — AI-powered weekly meal planning via Gemini."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, timedelta

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.meal_plan import MealPlan
from app.schemas.meal_plan import MealPlanResponse
from app.services.gemini import gemini_service

router = APIRouter(prefix="/mealplan", tags=["Meal Planning"])

VALID_GOALS = {"eat_clean", "weight_loss", "muscle_gain", "keto", "maintenance"}


class MealPlanRequest(BaseModel):
    goal: str = "eat_clean"
    days: int = Field(default=7, ge=1, le=14)
    calories_target: int = Field(default=2000, ge=1000, le=5000)


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
    try:
        ai_result = await gemini_service.generate_meal_plan(
            request.goal, request.days, request.calories_target
        )
    except Exception as e:
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

    # Return AI plan + DB id together
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
    result = await session.execute(
        select(MealPlan).where(MealPlan.user_id == user_id)
    )
    plans = result.scalars().all()
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
