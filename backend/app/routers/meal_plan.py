"""Meal plan router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.meal_plan import MealPlanGenerateRequest, MealPlanResponse
from app.models.meal_plan import MealPlan

router = APIRouter(prefix="/mealplan", tags=["Meal Planning"])


@router.post("/generate", response_model=MealPlanResponse)
async def generate_meal_plan(
    request: MealPlanGenerateRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> MealPlanResponse:
    """Generate a new meal plan using AI."""
    # TODO: Implement LLM-based meal plan generation
    # For now, create a placeholder meal plan

    meal_plan = MealPlan(
        user_id=user_id,
        title=f"Meal Plan ({request.start_date} to {request.end_date})",
        description="AI-generated meal plan",
        start_date=request.start_date,
        end_date=request.end_date,
        goal=request.goal,
        target_calories=request.target_calories,
    )

    session.add(meal_plan)
    await session.commit()
    await session.refresh(meal_plan)

    return MealPlanResponse(
        id=meal_plan.id,
        title=meal_plan.title,
        description=meal_plan.description,
        start_date=meal_plan.start_date,
        end_date=meal_plan.end_date,
        goal=meal_plan.goal,
        target_calories=meal_plan.target_calories,
        is_active=meal_plan.is_active,
        meal_items=[],
        created_at=meal_plan.created_at,
    )


@router.get("", response_model=List[MealPlanResponse])
async def get_meal_plans(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> List[MealPlanResponse]:
    """Get all meal plans for the current user."""
    statement = select(MealPlan).where(MealPlan.user_id == user_id)
    result = await session.execute(statement)
    meal_plans = result.scalars().all()

    return [
        MealPlanResponse(
            id=plan.id,
            title=plan.title,
            description=plan.description,
            start_date=plan.start_date,
            end_date=plan.end_date,
            goal=plan.goal,
            target_calories=plan.target_calories,
            is_active=plan.is_active,
            meal_items=[],  # TODO: Load meal items
            created_at=plan.created_at,
        )
        for plan in meal_plans
    ]
