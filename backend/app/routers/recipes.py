"""Recipe router."""
import time
from dataclasses import replace as dc_replace
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate, RecipeListResponse, RecipeResponse
from app.services.cache import cache_service
from app.services.llm import llm_provider
from app.services.memory_service import memory_service
from app.services.persona_context import PersonaContextResolver

router = APIRouter(prefix="/recipes", tags=["Recipes"])


# ── AI: suggest from ingredients ─────────────────────────────────────────────

class RecipeSuggestRequest(BaseModel):
    ingredients: List[str]
    filters: Optional[List[str]] = None
    persona_id: Optional[str] = None  # override active persona for this request


@router.post("/suggest")
async def suggest_recipes(
    request: RecipeSuggestRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Suggest dishes from given ingredients using Gemini 2.5 Flash."""
    if not request.ingredients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one ingredient is required",
        )
    logger.info(
        "router:suggest_recipes | ingredients_count={} filters_count={} persona_id={}",
        len(request.ingredients), len(request.filters or []), request.persona_id,
    )
    t0 = time.perf_counter()

    # Resolve persona
    resolver = PersonaContextResolver(session, cache_service)
    persona = await resolver.resolve(user_id, request.persona_id)

    # Inject user memory into recipe_prefix so suggestions respect restrictions
    memory_block = await memory_service.get_context_block(user_id, session, cache_service)
    if memory_block:
        persona = dc_replace(
            persona,
            recipe_prefix=persona.recipe_prefix + "\n\n" + memory_block,
        )

    try:
        result = await llm_provider.suggest_recipes(
            request.ingredients, request.filters or [], persona=persona
        )
        logger.info(
            "router:suggest_recipes | ok dishes_count={} latency={}ms",
            len(result.get("dishes", [])), round((time.perf_counter() - t0) * 1000, 1),
        )
        return result
    except Exception as e:
        logger.error(
            "router:suggest_recipes | error={} latency={}ms",
            str(e)[:200], round((time.perf_counter() - t0) * 1000, 1),
        )
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
    logger.debug(
        "db:list_recipes | search={} cuisine={} skip={} limit={}",
        search, cuisine, skip, limit,
    )
    t0 = time.perf_counter()
    statement = select(Recipe).where(Recipe.is_public == True)
    if search:
        statement = statement.where(Recipe.title.ilike(f"%{search}%"))
    if cuisine:
        statement = statement.where(Recipe.cuisine == cuisine)
    statement = statement.offset(skip).limit(limit)
    result = await session.execute(statement)
    rows = result.scalars().all()
    logger.info(
        "db:list_recipes | rows_returned={} latency={}ms",
        len(rows), round((time.perf_counter() - t0) * 1000, 1),
    )
    return rows


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    session: AsyncSession = Depends(get_session),
) -> RecipeResponse:
    """Get a specific saved recipe."""
    logger.debug("db:get_recipe | recipe_id={}", recipe_id)
    t0 = time.perf_counter()
    result = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = result.scalar_one_or_none()
    if not recipe:
        logger.warning("db:get_recipe | not_found recipe_id={}", recipe_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    recipe.view_count += 1
    await session.commit()
    logger.info(
        "db:get_recipe | found recipe_id={} title={} view_count={} latency={}ms",
        recipe_id, recipe.title, recipe.view_count,
        round((time.perf_counter() - t0) * 1000, 1),
    )
    return recipe


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> RecipeResponse:
    """Save a recipe."""
    logger.info("db:create_recipe | title={} cuisine={}", recipe_data.title, recipe_data.cuisine)
    t0 = time.perf_counter()
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
    logger.info(
        "db:create_recipe | ok recipe_id={} latency={}ms",
        recipe.id, round((time.perf_counter() - t0) * 1000, 1),
    )
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a saved recipe."""
    logger.info("db:delete_recipe | recipe_id={}", recipe_id)
    t0 = time.perf_counter()
    result = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    if recipe.author_id != user_id:
        logger.warning("db:delete_recipe | forbidden recipe_id={}", recipe_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    await session.delete(recipe)
    await session.commit()
    logger.info(
        "db:delete_recipe | ok recipe_id={} latency={}ms",
        recipe_id, round((time.perf_counter() - t0) * 1000, 1),
    )
