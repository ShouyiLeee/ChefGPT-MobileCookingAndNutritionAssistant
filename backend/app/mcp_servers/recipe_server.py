"""
RecipeMCPServer — tools for recipe search, suggestion, and management.

Tools:
  search_community_recipes       — semantic RAG search over 30 Vietnamese recipes
  get_community_recipe_detail    — get full recipe by index id
  suggest_recipes_from_ingredients — AI recipe suggestion (delegates to llm_provider)
  save_recipe                    — persist a recipe to user's saved list
  list_saved_recipes             — fetch user's saved recipes from DB
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

if TYPE_CHECKING:
    from app.services.cache import CacheService
    from app.services.llm.base_llm import BaseLLM
    from app.services.rag import RecipeRAGService
    from app.services.tool_registry import ToolRegistry


class RecipeMCPServer:
    """
    MCP server wrapping recipe-related operations.
    Call register_tools(registry) once in app lifespan to expose all tools.
    """

    def __init__(
        self,
        rag_service: "RecipeRAGService",
        llm_provider: "BaseLLM",
        cache_service: "CacheService",
    ) -> None:
        self._rag = rag_service
        self._llm = llm_provider
        self._cache = cache_service

    def register_tools(self, registry: "ToolRegistry") -> None:
        """Register all recipe tools into the central ToolRegistry."""
        registry.register("search_community_recipes", self.search_community_recipes)
        registry.register("get_community_recipe_detail", self.get_community_recipe_detail)
        registry.register("suggest_recipes_from_ingredients", self.suggest_recipes_from_ingredients)
        registry.register("save_recipe", self.save_recipe)
        registry.register("list_saved_recipes", self.list_saved_recipes)
        logger.info("RecipeMCPServer | registered 5 tools")

    # ── Tools ──────────────────────────────────────────────────────────────────

    async def search_community_recipes(
        self,
        query: str,
        cuisine: str | None = None,
        difficulty: str | None = None,
        k: int = 5,
    ) -> list[dict]:
        """
        Semantic search over the community recipe database.
        Uses Gemini embeddings for similarity, falls back to keyword matching.

        Args:
            query: Natural language search query (e.g. "canh chua cá")
            cuisine: Optional cuisine filter (e.g. "Vietnamese", "Thai")
            difficulty: Optional difficulty filter ("easy" | "medium" | "hard")
            k: Max number of results to return

        Returns:
            List of recipe cards with relevance score field.
        """
        logger.debug(
            "tool:search_community_recipes | query={} cuisine={} difficulty={} k={}",
            query, cuisine, difficulty, k,
        )
        if not self._rag.ready:
            logger.warning("tool:search_community_recipes | RAG not ready — falling back to keyword")
            return self._rag.keyword_search(query, cuisine=cuisine, difficulty=difficulty)

        # Semantic search first
        results = await self._rag.search(query, k=k)

        # Post-filter by cuisine/difficulty if specified
        if cuisine or difficulty:
            filtered = []
            for r in results:
                if cuisine and r.get("cuisine", "").lower() != cuisine.lower():
                    continue
                if difficulty and r.get("difficulty", "").lower() != difficulty.lower():
                    continue
                filtered.append(r)
            # If filter eliminates everything, return unfiltered semantic results
            results = filtered if filtered else results

        logger.debug(
            "tool:search_community_recipes | found={} query={}",
            len(results), query[:50],
        )
        return results

    async def get_community_recipe_detail(self, recipe_id: int) -> dict:
        """
        Get full recipe detail by its numeric id (0-indexed in the community list).

        Args:
            recipe_id: The recipe index from search results

        Returns:
            Full recipe dict with steps, ingredients, nutrition, etc.
        """
        logger.debug("tool:get_community_recipe_detail | recipe_id={}", recipe_id)
        recipes = self._rag._recipes
        if not recipes:
            return {"error": "Recipe database not available"}
        if not (0 <= recipe_id < len(recipes)):
            return {"error": f"Recipe id {recipe_id} out of range (0–{len(recipes) - 1})"}
        return recipes[recipe_id]

    async def suggest_recipes_from_ingredients(
        self,
        ingredients: list[str],
        filters: list[str] | None = None,
        persona_id: str | None = None,
    ) -> dict:
        """
        Generate AI recipe suggestions from available ingredients.
        Uses RAG context + Gemini, results are cached in Redis.

        Args:
            ingredients: List of available ingredient names
            filters: Optional dietary/cooking filters (e.g. ["chay", "ít dầu"])
            persona_id: Optional persona slug to apply cooking style

        Returns:
            {dishes: [{name, description, steps, time_minutes, difficulty, nutrition}]}
        """
        logger.debug(
            "tool:suggest_recipes_from_ingredients | ingredients={} filters={} persona_id={}",
            ingredients, filters, persona_id,
        )
        persona = None
        if persona_id:
            try:
                from app.services.persona_service import persona_service
                from app.services.persona_context import PersonaContext
                cfg = persona_service.get(persona_id)
                prompts = cfg.get("prompts", {})
                persona = PersonaContext(
                    persona_id=persona_id,
                    system_prompt=prompts.get("system", ""),
                    recipe_prefix=prompts.get("recipe_prefix", ""),
                    meal_plan_prefix=prompts.get("meal_plan_prefix", ""),
                    cuisine_filters=cfg.get("cuisine_filters", []),
                )
            except Exception as e:
                logger.warning("tool:suggest_recipes | persona_load_error={}", str(e)[:100])

        return await self._llm.suggest_recipes(ingredients, filters or [], persona)

    async def save_recipe(
        self,
        user_id: str,
        db: AsyncSession,
        title: str,
        description: str,
        cuisine: str = "Việt Nam",
        difficulty: str = "medium",
        prep_time: int = 15,
        cook_time: int = 30,
        servings: int = 2,
    ) -> dict:
        """
        Save a recipe to the user's personal recipe list.

        Args:
            user_id: Authenticated user ID (injected by agent, not from LLM)
            db: AsyncSession (injected by agent)
            title: Recipe name
            description: Short description
            cuisine: Cuisine type
            difficulty: "easy" | "medium" | "hard"
            prep_time: Preparation time in minutes
            cook_time: Cooking time in minutes
            servings: Number of servings

        Returns:
            {id, title, created_at}
        """
        from app.models.recipe import Recipe

        recipe = Recipe(
            user_id=user_id,
            title=title,
            description=description,
            cuisine=cuisine,
            difficulty=difficulty,
            prep_time=prep_time,
            cook_time=cook_time,
            servings=servings,
            is_public=False,
        )
        db.add(recipe)
        await db.commit()
        await db.refresh(recipe)
        logger.info("tool:save_recipe | user_id={} title={} id={}", user_id, title, recipe.id)
        return {"id": recipe.id, "title": recipe.title, "created_at": str(recipe.created_at)}

    async def list_saved_recipes(
        self,
        user_id: str,
        db: AsyncSession,
        search: str | None = None,
        cuisine: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Fetch the user's saved recipes from the database.

        Args:
            user_id: Authenticated user ID (injected by agent)
            db: AsyncSession (injected by agent)
            search: Optional text filter on title/description
            cuisine: Optional cuisine filter
            limit: Max results

        Returns:
            List of recipe summary dicts
        """
        from app.models.recipe import Recipe

        stmt = select(Recipe).where(Recipe.user_id == user_id).limit(limit)
        result = await db.execute(stmt)
        recipes = result.scalars().all()

        out = []
        for r in recipes:
            if search and search.lower() not in (r.title or "").lower():
                continue
            if cuisine and (r.cuisine or "").lower() != cuisine.lower():
                continue
            out.append({
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "cuisine": r.cuisine,
                "difficulty": r.difficulty,
                "prep_time": r.prep_time,
                "cook_time": r.cook_time,
                "servings": r.servings,
            })
        return out
