"""Recipe retrieval service for RAG-powered search."""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recipe import Recipe
from app.rag.vectorstore import vector_search
from app.rag.embeddings import embedding_service
from loguru import logger


class RecipeRetriever:
    """Service for retrieving recipes using RAG."""

    def __init__(self):
        """Initialize recipe retriever."""
        self.vector_search = vector_search
        self.embedding_service = embedding_service

    async def find_recipes_by_query(
        self,
        query: str,
        session: AsyncSession,
        limit: int = 10,
        filters: Dict[str, Any] | None = None,
        use_hybrid: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find recipes matching a text query.

        Args:
            query: Search query text
            session: Database session
            limit: Maximum number of results
            filters: Optional filters (cuisine, difficulty, etc.)
            use_hybrid: Whether to use hybrid search (semantic + keyword)

        Returns:
            List of recipe dictionaries with scores
        """
        try:
            if use_hybrid:
                results = await self.vector_search.hybrid_search(
                    query_text=query,
                    session=session,
                    limit=limit,
                )
            else:
                results = await self.vector_search.search_by_text(
                    query_text=query,
                    session=session,
                    limit=limit,
                    filters=filters,
                )

            # Format results
            recipes_with_meta = []
            for recipe, score in results:
                recipes_with_meta.append(
                    {
                        "recipe": recipe,
                        "score": score,
                        "match_reason": self._explain_match(query, recipe, score),
                    }
                )

            return recipes_with_meta

        except Exception as e:
            logger.error(f"Error finding recipes by query: {e}")
            return []

    async def find_recipes_by_ingredients(
        self,
        ingredients: List[str],
        session: AsyncSession,
        limit: int = 10,
        min_match_percentage: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Find recipes that can be made with given ingredients.

        Args:
            ingredients: List of available ingredients
            session: Database session
            limit: Maximum number of results
            min_match_percentage: Minimum percentage of ingredients that must match

        Returns:
            List of recipes with match information
        """
        try:
            results = await self.vector_search.search_by_ingredients(
                ingredients=ingredients,
                session=session,
                limit=limit,
            )

            # Calculate ingredient matching
            recipes_with_match = []
            for recipe, score in results:
                match_info = self._calculate_ingredient_match(
                    ingredients, recipe
                )

                if match_info["match_percentage"] >= min_match_percentage:
                    recipes_with_match.append(
                        {
                            "recipe": recipe,
                            "score": score,
                            "available_ingredients": match_info["available"],
                            "missing_ingredients": match_info["missing"],
                            "match_percentage": match_info["match_percentage"],
                        }
                    )

            # Sort by match percentage
            recipes_with_match.sort(
                key=lambda x: x["match_percentage"], reverse=True
            )

            return recipes_with_match[:limit]

        except Exception as e:
            logger.error(f"Error finding recipes by ingredients: {e}")
            return []

    async def get_recipe_recommendations(
        self,
        recipe_id: int,
        session: AsyncSession,
        limit: int = 5,
    ) -> List[Recipe]:
        """
        Get recipe recommendations based on a given recipe.

        Args:
            recipe_id: Recipe to base recommendations on
            session: Database session
            limit: Maximum number of recommendations

        Returns:
            List of similar recipes
        """
        try:
            results = await self.vector_search.find_similar_recipes(
                recipe_id=recipe_id,
                session=session,
                limit=limit,
            )

            return [recipe for recipe, _ in results]

        except Exception as e:
            logger.error(f"Error getting recipe recommendations: {e}")
            return []

    async def search_with_context(
        self,
        query: str,
        user_preferences: Dict[str, Any],
        session: AsyncSession,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search recipes with user context and preferences.

        Args:
            query: Search query
            user_preferences: User preferences (dietary restrictions, etc.)
            session: Database session
            limit: Maximum number of results

        Returns:
            List of contextually relevant recipes
        """
        # Build enhanced query with preferences
        enhanced_query = self._enhance_query_with_context(query, user_preferences)

        # Apply filters based on preferences
        filters = {}
        if "dietary_preference" in user_preferences:
            # Would need to filter based on dietary tags
            pass

        if "max_cook_time" in user_preferences:
            filters["max_prep_time"] = user_preferences["max_cook_time"]

        return await self.find_recipes_by_query(
            query=enhanced_query,
            session=session,
            limit=limit,
            filters=filters,
        )

    def _explain_match(self, query: str, recipe: Recipe, score: float) -> str:
        """
        Generate explanation for why a recipe matched the query.

        Args:
            query: Original query
            recipe: Matched recipe
            score: Match score

        Returns:
            Human-readable explanation
        """
        reasons = []

        # Check for direct title match
        if query.lower() in recipe.title.lower():
            reasons.append("matches recipe title")

        # Check for cuisine match
        if recipe.cuisine and query.lower() in recipe.cuisine.lower():
            reasons.append(f"is {recipe.cuisine} cuisine")

        # Check for category match
        if recipe.category and query.lower() in recipe.category.lower():
            reasons.append(f"is a {recipe.category} dish")

        # Add similarity score
        if score > 0.9:
            reasons.append("very high similarity")
        elif score > 0.8:
            reasons.append("high similarity")
        elif score > 0.7:
            reasons.append("good similarity")

        return ", ".join(reasons) if reasons else "semantic similarity"

    def _calculate_ingredient_match(
        self, user_ingredients: List[str], recipe: Recipe
    ) -> Dict[str, Any]:
        """
        Calculate how well user's ingredients match a recipe.

        Args:
            user_ingredients: User's available ingredients
            recipe: Recipe to match against

        Returns:
            Dictionary with match information
        """
        # TODO: Load recipe ingredients from database
        # For now, return placeholder
        recipe_ingredients = []  # Would load from recipe.recipe_ingredients

        if not recipe_ingredients:
            return {
                "available": [],
                "missing": [],
                "match_percentage": 0.0,
            }

        # Normalize ingredient names for matching
        user_ing_lower = [ing.lower().strip() for ing in user_ingredients]
        recipe_ing_lower = [ing.lower().strip() for ing in recipe_ingredients]

        # Find matches
        available = [
            ing for ing in recipe_ingredients if ing.lower() in user_ing_lower
        ]
        missing = [
            ing for ing in recipe_ingredients if ing.lower() not in user_ing_lower
        ]

        match_percentage = (
            len(available) / len(recipe_ingredients) if recipe_ingredients else 0.0
        )

        return {
            "available": available,
            "missing": missing,
            "match_percentage": match_percentage,
        }

    def _enhance_query_with_context(
        self, query: str, preferences: Dict[str, Any]
    ) -> str:
        """
        Enhance query with user preferences and context.

        Args:
            query: Original query
            preferences: User preferences

        Returns:
            Enhanced query string
        """
        enhancements = []

        if "dietary_preference" in preferences:
            enhancements.append(preferences["dietary_preference"])

        if "goal" in preferences:
            goal_map = {
                "weight_loss": "healthy low-calorie",
                "muscle_gain": "high-protein",
                "maintenance": "balanced",
            }
            if preferences["goal"] in goal_map:
                enhancements.append(goal_map[preferences["goal"]])

        if enhancements:
            return f"{query} {' '.join(enhancements)}"

        return query


# Global recipe retriever instance
recipe_retriever = RecipeRetriever()
