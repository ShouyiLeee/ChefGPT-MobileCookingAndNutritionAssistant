"""Recipe router."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.recipe import RecipeCreate, RecipeResponse, RecipeListResponse
from app.models.recipe import Recipe
from app.services.llm import llm_provider

router = APIRouter(prefix="/recipes", tags=["Recipes"])


# ── AI: suggest from ingredients ─────────────────────────────────────────────

class RecipeSuggestRequest(BaseModel):
    ingredients: List[str]
    filters: Optional[List[str]] = None


@router.post("/suggest")
async def suggest_recipes(
    request: RecipeSuggestRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Suggest dishes from given ingredients using Gemini 2.5 Flash."""
    if not request.ingredients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one ingredient is required",
        )
    try:
        return await llm_provider.suggest_recipes(
            request.ingredients, request.filters or []
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )


# ── CRUD: saved recipes ───────────────────────────────────────────────────────

@router.get("", response_model=List[RecipeListResponse])
async def list_recipes(
    search: Optional[str] = Query(None),
    cuisine: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> List[RecipeListResponse]:
    """List saved recipes."""
    statement = select(Recipe).where(Recipe.is_public == True)
    if search:
        statement = statement.where(Recipe.title.ilike(f"%{search}%"))
    if cuisine:
        statement = statement.where(Recipe.cuisine == cuisine)
    statement = statement.offset(skip).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    session: AsyncSession = Depends(get_session),
) -> RecipeResponse:
    """Get a specific saved recipe."""
    result = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    recipe.view_count += 1
    await session.commit()
    return recipe


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> RecipeResponse:
    """Save a recipe."""
    total_time = (recipe_data.prep_time or 0) + (recipe_data.cook_time or 0)
    recipe = Recipe(
        author_id=user_id,
        title=recipe_data.title,
        description=recipe_data.description,
        image_url=recipe_data.image_url,
        prep_time=recipe_data.prep_time,
        cook_time=recipe_data.cook_time,
        total_time=total_time or None,
        servings=recipe_data.servings,
        difficulty=recipe_data.difficulty,
        cuisine=recipe_data.cuisine,
        category=recipe_data.category,
    )
    session.add(recipe)
    await session.commit()
    await session.refresh(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a saved recipe."""
    result = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    if recipe.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    await session.delete(recipe)
    await session.commit()
