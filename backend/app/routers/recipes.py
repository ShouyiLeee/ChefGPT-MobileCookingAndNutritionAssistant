"""Recipe router."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeListResponse,
)
from app.models.recipe import Recipe, RecipeIngredient, RecipeStep, Ingredient

router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.get("", response_model=List[RecipeListResponse])
async def list_recipes(
    search: Optional[str] = Query(None),
    cuisine: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> List[RecipeListResponse]:
    """List all recipes with optional filters."""
    statement = select(Recipe).where(Recipe.is_public == True)

    if search:
        statement = statement.where(Recipe.title.ilike(f"%{search}%"))

    if cuisine:
        statement = statement.where(Recipe.cuisine == cuisine)

    if difficulty:
        statement = statement.where(Recipe.difficulty == difficulty)

    statement = statement.offset(skip).limit(limit)

    result = await session.execute(statement)
    recipes = result.scalars().all()

    return recipes


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    session: AsyncSession = Depends(get_session),
) -> RecipeResponse:
    """Get a specific recipe by ID."""
    statement = select(Recipe).where(Recipe.id == recipe_id)
    result = await session.execute(statement)
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    # Increment view count
    recipe.view_count += 1
    await session.commit()

    return recipe


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> RecipeResponse:
    """Create a new recipe."""
    # Calculate total time
    total_time = (recipe_data.prep_time or 0) + (recipe_data.cook_time or 0)

    # Create recipe
    recipe = Recipe(
        author_id=user_id,
        title=recipe_data.title,
        description=recipe_data.description,
        image_url=recipe_data.image_url,
        video_url=recipe_data.video_url,
        prep_time=recipe_data.prep_time,
        cook_time=recipe_data.cook_time,
        total_time=total_time if total_time > 0 else None,
        servings=recipe_data.servings,
        difficulty=recipe_data.difficulty,
        cuisine=recipe_data.cuisine,
        category=recipe_data.category,
    )

    session.add(recipe)
    await session.flush()

    # TODO: Add ingredients and steps
    # This requires ingredient lookup/creation logic

    await session.commit()
    await session.refresh(recipe)

    return recipe


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    recipe_data: RecipeUpdate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> RecipeResponse:
    """Update a recipe."""
    statement = select(Recipe).where(Recipe.id == recipe_id)
    result = await session.execute(statement)
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    if recipe.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this recipe",
        )

    # Update fields
    update_data = recipe_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(recipe, key, value)

    # Recalculate total time if prep or cook time changed
    if "prep_time" in update_data or "cook_time" in update_data:
        recipe.total_time = (recipe.prep_time or 0) + (recipe.cook_time or 0)

    await session.commit()
    await session.refresh(recipe)

    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a recipe."""
    statement = select(Recipe).where(Recipe.id == recipe_id)
    result = await session.execute(statement)
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    if recipe.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this recipe",
        )

    await session.delete(recipe)
    await session.commit()
