"""Vector store for RAG (Retrieval Augmented Generation)."""
from typing import List, Dict, Any, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recipe import Recipe
from app.llm.client import llm_client
from app.core.config import settings


class VectorStore:
    """Vector store for recipe embeddings."""

    def __init__(self):
        """Initialize vector store."""
        self.dimension = settings.embedding_dimension

    async def add_recipe(self, recipe: Recipe, session: AsyncSession) -> None:
        """
        Add or update a recipe in the vector store.

        Args:
            recipe: Recipe to add
            session: Database session
        """
        # Create text representation of recipe
        recipe_text = self._create_recipe_text(recipe)

        # Generate embedding
        embedding = await llm_client.get_embedding(recipe_text)

        # Update recipe with embedding
        recipe.embedding = embedding
        await session.commit()

    async def search(
        self,
        query: str,
        session: AsyncSession,
        limit: int = 10,
    ) -> List[Recipe]:
        """
        Search for similar recipes using vector similarity.

        Args:
            query: Search query
            session: Database session
            limit: Maximum number of results

        Returns:
            List of matching recipes
        """
        # Generate query embedding
        query_embedding = await llm_client.get_embedding(query)

        # TODO: Implement pgvector similarity search
        # This would use cosine similarity or L2 distance
        # Example SQL: ORDER BY embedding <=> query_embedding LIMIT limit

        # For now, return placeholder
        statement = select(Recipe).where(Recipe.is_public == True).limit(limit)
        result = await session.execute(statement)
        recipes = result.scalars().all()

        return list(recipes)

    async def search_by_ingredients(
        self,
        ingredients: List[str],
        session: AsyncSession,
        limit: int = 10,
    ) -> List[Recipe]:
        """
        Search for recipes by ingredient list.

        Args:
            ingredients: List of ingredients
            session: Database session
            limit: Maximum number of results

        Returns:
            List of matching recipes
        """
        # Create query from ingredients
        query = f"Recipe with {', '.join(ingredients)}"

        return await self.search(query, session, limit)

    def _create_recipe_text(self, recipe: Recipe) -> str:
        """
        Create searchable text representation of recipe.

        Args:
            recipe: Recipe to convert

        Returns:
            Text representation
        """
        parts = [
            f"Title: {recipe.title}",
            f"Description: {recipe.description}",
        ]

        if recipe.cuisine:
            parts.append(f"Cuisine: {recipe.cuisine}")

        if recipe.category:
            parts.append(f"Category: {recipe.category}")

        if recipe.difficulty:
            parts.append(f"Difficulty: {recipe.difficulty}")

        # TODO: Add ingredients and steps

        return " | ".join(parts)


# Global vector store instance
vector_store = VectorStore()
