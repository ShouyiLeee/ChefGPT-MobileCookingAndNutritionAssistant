"""RAG-powered recipe search tools for LLM agents."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.recipe.recipe_retriever import recipe_retriever
from loguru import logger


async def search_recipes_semantic(
    query: str,
    session: AsyncSession,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search for recipes using semantic search (RAG).

    This tool uses vector embeddings to find recipes that semantically match
    the query, even if exact keywords don't appear in the recipe.

    Args:
        query: Natural language search query
        session: Database session
        max_results: Maximum number of results to return

    Returns:
        List of recipe dictionaries with metadata
    """
    try:
        results = await recipe_retriever.find_recipes_by_query(
            query=query,
            session=session,
            limit=max_results,
            use_hybrid=True,
        )

        # Format for LLM consumption
        formatted_results = []
        for result in results:
            recipe = result["recipe"]
            formatted_results.append(
                {
                    "id": recipe.id,
                    "title": recipe.title,
                    "description": recipe.description[:200] if recipe.description else "",
                    "cuisine": recipe.cuisine,
                    "difficulty": recipe.difficulty,
                    "prep_time": recipe.prep_time,
                    "cook_time": recipe.cook_time,
                    "match_score": round(result["score"], 2),
                    "match_reason": result["match_reason"],
                }
            )

        return formatted_results

    except Exception as e:
        logger.error(f"Error in semantic recipe search: {e}")
        return []


async def find_recipes_by_ingredients_rag(
    ingredients: List[str],
    session: AsyncSession,
    max_results: int = 5,
    min_match: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Find recipes that can be made with available ingredients using RAG.

    This tool uses semantic understanding to match ingredient names and
    find recipes even with similar or substitute ingredients.

    Args:
        ingredients: List of available ingredient names
        session: Database session
        max_results: Maximum number of results
        min_match: Minimum percentage of ingredients that must match (0.0-1.0)

    Returns:
        List of recipes with ingredient match information
    """
    try:
        results = await recipe_retriever.find_recipes_by_ingredients(
            ingredients=ingredients,
            session=session,
            limit=max_results,
            min_match_percentage=min_match,
        )

        # Format results
        formatted_results = []
        for result in results:
            recipe = result["recipe"]
            formatted_results.append(
                {
                    "id": recipe.id,
                    "title": recipe.title,
                    "description": recipe.description[:200] if recipe.description else "",
                    "match_percentage": round(result["match_percentage"] * 100, 1),
                    "available_ingredients": result["available_ingredients"],
                    "missing_ingredients": result["missing_ingredients"],
                    "can_substitute": len(result["missing_ingredients"]) <= 2,
                }
            )

        return formatted_results

    except Exception as e:
        logger.error(f"Error finding recipes by ingredients: {e}")
        return []


async def get_similar_recipes_rag(
    recipe_id: int,
    session: AsyncSession,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Get recipes similar to a given recipe using RAG.

    Uses vector similarity to find recipes with similar ingredients,
    cooking methods, or flavor profiles.

    Args:
        recipe_id: ID of the recipe to find similar recipes for
        session: Database session
        max_results: Maximum number of similar recipes

    Returns:
        List of similar recipe dictionaries
    """
    try:
        recipes = await recipe_retriever.get_recipe_recommendations(
            recipe_id=recipe_id,
            session=session,
            limit=max_results,
        )

        # Format results
        formatted_results = []
        for recipe in recipes:
            formatted_results.append(
                {
                    "id": recipe.id,
                    "title": recipe.title,
                    "description": recipe.description[:200] if recipe.description else "",
                    "cuisine": recipe.cuisine,
                    "difficulty": recipe.difficulty,
                    "reason": "Similar ingredients or cooking style",
                }
            )

        return formatted_results

    except Exception as e:
        logger.error(f"Error getting similar recipes: {e}")
        return []


async def search_recipes_with_context(
    query: str,
    user_preferences: Dict[str, Any],
    session: AsyncSession,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search recipes considering user preferences and dietary restrictions.

    This tool enhances the search with user context like dietary preferences,
    health goals, and restrictions.

    Args:
        query: Search query
        user_preferences: Dictionary with user preferences
            - dietary_preference: vegetarian, vegan, etc.
            - goal: weight_loss, muscle_gain, maintenance
            - allergies: List of allergies
            - max_cook_time: Maximum cooking time in minutes
        session: Database session
        max_results: Maximum number of results

    Returns:
        List of contextually relevant recipes
    """
    try:
        results = await recipe_retriever.search_with_context(
            query=query,
            user_preferences=user_preferences,
            session=session,
            limit=max_results,
        )

        # Format results
        formatted_results = []
        for result in results:
            recipe = result["recipe"]
            formatted_results.append(
                {
                    "id": recipe.id,
                    "title": recipe.title,
                    "description": recipe.description[:200] if recipe.description else "",
                    "cuisine": recipe.cuisine,
                    "difficulty": recipe.difficulty,
                    "prep_time": recipe.prep_time,
                    "cook_time": recipe.cook_time,
                    "match_score": round(result["score"], 2),
                    "personalized": True,
                }
            )

        return formatted_results

    except Exception as e:
        logger.error(f"Error in contextual recipe search: {e}")
        return []


# Tool descriptions for LLM
RECIPE_SEARCH_TOOLS = {
    "search_recipes_semantic": {
        "name": "search_recipes_semantic",
        "description": "Search for recipes using natural language. Returns semantically similar recipes even if exact keywords don't match.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query (e.g., 'healthy breakfast', 'Vietnamese soup')",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    "find_recipes_by_ingredients_rag": {
        "name": "find_recipes_by_ingredients_rag",
        "description": "Find recipes that can be made with available ingredients. Shows which ingredients are available and which are missing.",
        "parameters": {
            "type": "object",
            "properties": {
                "ingredients": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of available ingredients",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5,
                },
                "min_match": {
                    "type": "number",
                    "description": "Minimum match percentage (0.0-1.0)",
                    "default": 0.5,
                },
            },
            "required": ["ingredients"],
        },
    },
    "get_similar_recipes_rag": {
        "name": "get_similar_recipes_rag",
        "description": "Get recipes similar to a given recipe. Useful for recommendations.",
        "parameters": {
            "type": "object",
            "properties": {
                "recipe_id": {
                    "type": "integer",
                    "description": "ID of the recipe to find similar recipes for",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of similar recipes",
                    "default": 5,
                },
            },
            "required": ["recipe_id"],
        },
    },
}
