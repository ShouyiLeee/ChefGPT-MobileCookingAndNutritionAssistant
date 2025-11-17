"""Vector search functionality using pgvector."""
from typing import List, Dict, Any, Optional, Tuple
from sqlmodel import select, text, col
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recipe import Recipe
from app.rag.embeddings import embedding_service
from loguru import logger


class VectorSearch:
    """Vector similarity search for recipes."""

    def __init__(self):
        """Initialize vector search."""
        self.embedding_service = embedding_service

    async def search_similar_recipes(
        self,
        query_embedding: List[float],
        session: AsyncSession,
        limit: int = 10,
        threshold: float = 0.7,
        filters: Dict[str, Any] | None = None,
    ) -> List[Tuple[Recipe, float]]:
        """
        Search for similar recipes using vector similarity.

        Args:
            query_embedding: Query embedding vector
            session: Database session
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0-1)
            filters: Optional filters (cuisine, difficulty, etc.)

        Returns:
            List of (Recipe, similarity_score) tuples
        """
        try:
            # Build base query with cosine distance
            # pgvector uses <=> for cosine distance (0 = identical, 2 = opposite)
            # Convert to similarity: 1 - (distance / 2)

            # Use raw SQL for pgvector operations
            query = """
                SELECT
                    *,
                    1 - (embedding <=> :query_embedding::vector) AS similarity
                FROM recipes
                WHERE
                    embedding IS NOT NULL
                    AND is_public = true
                    AND (1 - (embedding <=> :query_embedding::vector)) >= :threshold
            """

            # Add filters
            conditions = []
            params = {
                "query_embedding": query_embedding,
                "threshold": threshold,
            }

            if filters:
                if "cuisine" in filters:
                    conditions.append("cuisine = :cuisine")
                    params["cuisine"] = filters["cuisine"]

                if "difficulty" in filters:
                    conditions.append("difficulty = :difficulty")
                    params["difficulty"] = filters["difficulty"]

                if "max_prep_time" in filters:
                    conditions.append("prep_time <= :max_prep_time")
                    params["max_prep_time"] = filters["max_prep_time"]

                if "category" in filters:
                    conditions.append("category = :category")
                    params["category"] = filters["category"]

            if conditions:
                query += " AND " + " AND ".join(conditions)

            query += " ORDER BY similarity DESC LIMIT :limit"
            params["limit"] = limit

            # Execute query
            result = await session.execute(text(query), params)
            rows = result.fetchall()

            # Convert to Recipe objects
            recipes_with_scores = []
            for row in rows:
                # Create Recipe object from row
                recipe = Recipe.from_orm(row)
                similarity = row.similarity
                recipes_with_scores.append((recipe, float(similarity)))

            return recipes_with_scores

        except Exception as e:
            logger.error(f"Error searching similar recipes: {e}")
            return []

    async def search_by_text(
        self,
        query_text: str,
        session: AsyncSession,
        limit: int = 10,
        threshold: float = 0.7,
        filters: Dict[str, Any] | None = None,
    ) -> List[Tuple[Recipe, float]]:
        """
        Search recipes by text query.

        Args:
            query_text: Search query text
            session: Database session
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            filters: Optional filters

        Returns:
            List of (Recipe, similarity_score) tuples
        """
        # Generate embedding for query
        query_embedding = await self.embedding_service.generate_embedding(query_text)

        # Search using embedding
        return await self.search_similar_recipes(
            query_embedding=query_embedding,
            session=session,
            limit=limit,
            threshold=threshold,
            filters=filters,
        )

    async def search_by_ingredients(
        self,
        ingredients: List[str],
        session: AsyncSession,
        limit: int = 10,
        threshold: float = 0.6,
    ) -> List[Tuple[Recipe, float]]:
        """
        Search recipes by ingredient list.

        Args:
            ingredients: List of ingredient names
            session: Database session
            limit: Maximum number of results
            threshold: Minimum similarity threshold

        Returns:
            List of (Recipe, similarity_score) tuples
        """
        # Create query text from ingredients
        query_text = f"Recipe with ingredients: {', '.join(ingredients)}"

        return await self.search_by_text(
            query_text=query_text,
            session=session,
            limit=limit,
            threshold=threshold,
        )

    async def find_similar_recipes(
        self,
        recipe_id: int,
        session: AsyncSession,
        limit: int = 5,
    ) -> List[Tuple[Recipe, float]]:
        """
        Find recipes similar to a given recipe.

        Args:
            recipe_id: Recipe ID to find similar recipes for
            session: Database session
            limit: Maximum number of results

        Returns:
            List of (Recipe, similarity_score) tuples
        """
        # Get the recipe
        statement = select(Recipe).where(Recipe.id == recipe_id)
        result = await session.execute(statement)
        recipe = result.scalar_one_or_none()

        if not recipe or not recipe.embedding:
            return []

        # Search for similar recipes (exclude the recipe itself)
        query = """
            SELECT
                *,
                1 - (embedding <=> :query_embedding::vector) AS similarity
            FROM recipes
            WHERE
                embedding IS NOT NULL
                AND is_public = true
                AND id != :recipe_id
            ORDER BY similarity DESC
            LIMIT :limit
        """

        result = await session.execute(
            text(query),
            {
                "query_embedding": recipe.embedding,
                "recipe_id": recipe_id,
                "limit": limit,
            },
        )
        rows = result.fetchall()

        recipes_with_scores = []
        for row in rows:
            similar_recipe = Recipe.from_orm(row)
            similarity = row.similarity
            recipes_with_scores.append((similar_recipe, float(similarity)))

        return recipes_with_scores

    async def hybrid_search(
        self,
        query_text: str,
        session: AsyncSession,
        limit: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[Tuple[Recipe, float]]:
        """
        Hybrid search combining semantic and keyword search.

        Args:
            query_text: Search query
            session: Database session
            limit: Maximum number of results
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)

        Returns:
            List of (Recipe, combined_score) tuples
        """
        # Generate embedding
        query_embedding = await self.embedding_service.generate_embedding(query_text)

        # Hybrid search with both semantic and keyword matching
        query = """
            WITH semantic_scores AS (
                SELECT
                    id,
                    1 - (embedding <=> :query_embedding::vector) AS semantic_score
                FROM recipes
                WHERE embedding IS NOT NULL AND is_public = true
            ),
            keyword_scores AS (
                SELECT
                    id,
                    ts_rank(
                        to_tsvector('english', title || ' ' || description),
                        plainto_tsquery('english', :query_text)
                    ) AS keyword_score
                FROM recipes
                WHERE is_public = true
            )
            SELECT
                r.*,
                (
                    COALESCE(s.semantic_score, 0) * :semantic_weight +
                    COALESCE(k.keyword_score, 0) * :keyword_weight
                ) AS combined_score
            FROM recipes r
            LEFT JOIN semantic_scores s ON r.id = s.id
            LEFT JOIN keyword_scores k ON r.id = k.id
            WHERE r.is_public = true
            ORDER BY combined_score DESC
            LIMIT :limit
        """

        result = await session.execute(
            text(query),
            {
                "query_embedding": query_embedding,
                "query_text": query_text,
                "semantic_weight": semantic_weight,
                "keyword_weight": keyword_weight,
                "limit": limit,
            },
        )
        rows = result.fetchall()

        recipes_with_scores = []
        for row in rows:
            recipe = Recipe.from_orm(row)
            score = row.combined_score
            recipes_with_scores.append((recipe, float(score)))

        return recipes_with_scores


# Global vector search instance
vector_search = VectorSearch()
