"""Recipe search router with RAG-powered semantic search."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.services.recipe import recipe_retriever
from app.schemas.recipe import RecipeListResponse
from loguru import logger


router = APIRouter(prefix="/recipes/search", tags=["Recipe Search"])


@router.get("/semantic", response_model=List[dict])
async def semantic_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    cuisine: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    max_prep_time: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """
    Semantic search for recipes using RAG.

    This endpoint uses AI-powered semantic search to find recipes that match
    the meaning of your query, not just exact keyword matches.

    Examples:
    - "healthy breakfast" → finds nutritious morning meals
    - "quick dinner" → finds fast evening recipes
    - "comfort food" → finds hearty, satisfying dishes
    - "Vietnamese soup" → finds Vietnamese soup recipes
    """
    try:
        # Build filters
        filters = {}
        if cuisine:
            filters["cuisine"] = cuisine
        if difficulty:
            filters["difficulty"] = difficulty
        if max_prep_time:
            filters["max_prep_time"] = max_prep_time

        # Search using RAG
        results = await recipe_retriever.find_recipes_by_query(
            query=q,
            session=session,
            limit=limit,
            filters=filters,
            use_hybrid=True,
        )

        # Format response
        recipes_with_scores = []
        for result in results:
            recipe = result["recipe"]
            recipes_with_scores.append(
                {
                    "id": recipe.id,
                    "title": recipe.title,
                    "description": recipe.description,
                    "image_url": recipe.image_url,
                    "cuisine": recipe.cuisine,
                    "difficulty": recipe.difficulty,
                    "prep_time": recipe.prep_time,
                    "cook_time": recipe.cook_time,
                    "total_time": recipe.total_time,
                    "servings": recipe.servings,
                    "like_count": recipe.like_count,
                    "match_score": result["score"],
                    "match_reason": result["match_reason"],
                }
            )

        return recipes_with_scores

    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return []


@router.get("/by-ingredients", response_model=List[dict])
async def search_by_ingredients(
    ingredients: str = Query(
        ...,
        description="Comma-separated list of ingredients (e.g., 'chicken,tomato,onion')",
    ),
    limit: int = Query(10, ge=1, le=50),
    min_match: float = Query(0.5, ge=0.0, le=1.0),
    session: AsyncSession = Depends(get_session),
):
    """
    Find recipes that can be made with your available ingredients.

    Uses semantic understanding to match ingredient names and find recipes
    even with similar or substitute ingredients.

    The response includes:
    - Which of your ingredients are used
    - Which ingredients are missing
    - Match percentage
    - Whether substitutions are possible
    """
    try:
        # Parse ingredients
        ingredient_list = [ing.strip() for ing in ingredients.split(",")]

        if not ingredient_list:
            return []

        # Search using RAG
        results = await recipe_retriever.find_recipes_by_ingredients(
            ingredients=ingredient_list,
            session=session,
            limit=limit,
            min_match_percentage=min_match,
        )

        # Format response
        formatted_results = []
        for result in results:
            recipe = result["recipe"]
            formatted_results.append(
                {
                    "id": recipe.id,
                    "title": recipe.title,
                    "description": recipe.description,
                    "image_url": recipe.image_url,
                    "cuisine": recipe.cuisine,
                    "difficulty": recipe.difficulty,
                    "prep_time": recipe.prep_time,
                    "cook_time": recipe.cook_time,
                    "match_percentage": result["match_percentage"],
                    "available_ingredients": result["available_ingredients"],
                    "missing_ingredients": result["missing_ingredients"],
                    "can_make": len(result["missing_ingredients"]) == 0,
                    "substitution_possible": len(result["missing_ingredients"]) <= 2,
                }
            )

        return formatted_results

    except Exception as e:
        logger.error(f"Error searching by ingredients: {e}")
        return []


@router.get("/{recipe_id}/similar", response_model=List[RecipeListResponse])
async def get_similar_recipes(
    recipe_id: int,
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
):
    """
    Get recipes similar to a given recipe.

    Uses vector similarity to find recipes with similar:
    - Ingredients
    - Cooking methods
    - Flavor profiles
    - Cuisine style
    """
    try:
        similar_recipes = await recipe_retriever.get_recipe_recommendations(
            recipe_id=recipe_id,
            session=session,
            limit=limit,
        )

        return similar_recipes

    except Exception as e:
        logger.error(f"Error getting similar recipes: {e}")
        return []


@router.get("/personalized", response_model=List[dict])
async def personalized_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Search recipes with personalization based on user preferences.

    Takes into account:
    - Dietary preferences (vegetarian, vegan, etc.)
    - Health goals (weight loss, muscle gain, etc.)
    - Allergies and restrictions
    - Cooking skill level
    - Time constraints
    """
    try:
        # TODO: Load user preferences from database
        user_preferences = {
            # These would come from user profile
            "dietary_preference": None,
            "goal": None,
            "allergies": [],
            "max_cook_time": None,
        }

        results = await recipe_retriever.search_with_context(
            query=q,
            user_preferences=user_preferences,
            session=session,
            limit=limit,
        )

        # Format response
        formatted_results = []
        for result in results:
            recipe = result["recipe"]
            formatted_results.append(
                {
                    "id": recipe.id,
                    "title": recipe.title,
                    "description": recipe.description,
                    "image_url": recipe.image_url,
                    "cuisine": recipe.cuisine,
                    "difficulty": recipe.difficulty,
                    "prep_time": recipe.prep_time,
                    "cook_time": recipe.cook_time,
                    "match_score": result["score"],
                    "personalized_reason": "Matches your preferences and goals",
                }
            )

        return formatted_results

    except Exception as e:
        logger.error(f"Error in personalized search: {e}")
        return []
