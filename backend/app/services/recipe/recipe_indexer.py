"""Recipe indexing service for RAG pipeline."""
from typing import List, Optional, Dict
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recipe import Recipe
from app.rag.embeddings import embedding_service
from loguru import logger


class RecipeIndexer:
    """Service for indexing recipes with embeddings."""

    def __init__(self):
        """Initialize recipe indexer."""
        self.embedding_service = embedding_service

    async def index_recipe(self, recipe: Recipe, session: AsyncSession) -> bool:
        """
        Index a single recipe by generating and storing its embedding.

        Args:
            recipe: Recipe to index
            session: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create searchable text representation
            recipe_text = self._create_recipe_text(recipe)

            # Generate embedding
            embedding = await self.embedding_service.generate_embedding(recipe_text)

            # Update recipe with embedding
            recipe.embedding = embedding

            await session.commit()
            await session.refresh(recipe)

            logger.info(f"Successfully indexed recipe {recipe.id}: {recipe.title}")
            return True

        except Exception as e:
            logger.error(f"Error indexing recipe {recipe.id}: {e}")
            await session.rollback()
            return False

    async def index_recipes_batch(
        self,
        recipe_ids: List[int],
        session: AsyncSession,
    ) -> Dict[str, int]:
        """
        Index multiple recipes in batch.

        Args:
            recipe_ids: List of recipe IDs to index
            session: Database session

        Returns:
            Dictionary with success and failure counts
        """
        results = {"success": 0, "failed": 0, "skipped": 0}

        # Fetch recipes
        statement = select(Recipe).where(Recipe.id.in_(recipe_ids))
        result = await session.execute(statement)
        recipes = result.scalars().all()

        if not recipes:
            logger.warning(f"No recipes found for IDs: {recipe_ids}")
            return results

        # Create text representations
        recipe_texts = []
        valid_recipes = []

        for recipe in recipes:
            try:
                recipe_text = self._create_recipe_text(recipe)
                recipe_texts.append(recipe_text)
                valid_recipes.append(recipe)
            except Exception as e:
                logger.error(f"Error creating text for recipe {recipe.id}: {e}")
                results["failed"] += 1

        if not recipe_texts:
            return results

        try:
            # Generate embeddings in batch
            embeddings = await self.embedding_service.generate_embeddings_batch(
                recipe_texts
            )

            # Update recipes with embeddings
            for recipe, embedding in zip(valid_recipes, embeddings):
                recipe.embedding = embedding
                results["success"] += 1

            await session.commit()

            logger.info(
                f"Successfully indexed {results['success']} recipes in batch"
            )

        except Exception as e:
            logger.error(f"Error in batch indexing: {e}")
            await session.rollback()
            results["failed"] += len(valid_recipes)
            results["success"] = 0

        return results

    async def reindex_all_recipes(self, session: AsyncSession) -> Dict[str, int]:
        """
        Reindex all public recipes.

        Args:
            session: Database session

        Returns:
            Dictionary with indexing statistics
        """
        logger.info("Starting full recipe reindexing...")

        # Get all public recipes without embeddings or with old embeddings
        statement = select(Recipe).where(Recipe.is_public == True)
        result = await session.execute(statement)
        recipes = result.scalars().all()

        recipe_ids = [recipe.id for recipe in recipes]

        if not recipe_ids:
            logger.info("No recipes to index")
            return {"success": 0, "failed": 0, "skipped": 0}

        # Process in batches
        batch_size = 50
        total_results = {"success": 0, "failed": 0, "skipped": 0}

        for i in range(0, len(recipe_ids), batch_size):
            batch_ids = recipe_ids[i : i + batch_size]
            batch_results = await self.index_recipes_batch(batch_ids, session)

            total_results["success"] += batch_results["success"]
            total_results["failed"] += batch_results["failed"]
            total_results["skipped"] += batch_results["skipped"]

            logger.info(
                f"Processed batch {i//batch_size + 1}: "
                f"{batch_results['success']} success, {batch_results['failed']} failed"
            )

        logger.info(f"Reindexing complete: {total_results}")
        return total_results

    def _create_recipe_text(self, recipe: Recipe) -> str:
        """
        Create searchable text representation of a recipe.

        Args:
            recipe: Recipe to convert

        Returns:
            Text representation optimized for search
        """
        parts = []

        # Title (most important)
        parts.append(f"Title: {recipe.title}")

        # Description
        if recipe.description:
            parts.append(f"Description: {recipe.description}")

        # Cuisine and category
        if recipe.cuisine:
            parts.append(f"Cuisine: {recipe.cuisine}")

        if recipe.category:
            parts.append(f"Category: {recipe.category}")

        # Difficulty
        if recipe.difficulty:
            parts.append(f"Difficulty: {recipe.difficulty}")

        # Cooking times
        if recipe.prep_time:
            parts.append(f"Preparation time: {recipe.prep_time} minutes")

        if recipe.cook_time:
            parts.append(f"Cooking time: {recipe.cook_time} minutes")

        # Servings
        if recipe.servings:
            parts.append(f"Servings: {recipe.servings}")

        # Tags
        if recipe.tags:
            parts.append(f"Tags: {recipe.tags}")

        # TODO: Add ingredients when loaded
        # if recipe.recipe_ingredients:
        #     ingredients = [ing.ingredient.name for ing in recipe.recipe_ingredients]
        #     parts.append(f"Ingredients: {', '.join(ingredients)}")

        # TODO: Add steps summary when loaded
        # if recipe.steps:
        #     steps_text = " ".join([step.instruction for step in recipe.steps[:3]])
        #     parts.append(f"Instructions: {steps_text}")

        return " | ".join(parts)

    async def remove_embedding(self, recipe_id: int, session: AsyncSession) -> bool:
        """
        Remove embedding from a recipe.

        Args:
            recipe_id: Recipe ID
            session: Database session

        Returns:
            True if successful
        """
        try:
            statement = select(Recipe).where(Recipe.id == recipe_id)
            result = await session.execute(statement)
            recipe = result.scalar_one_or_none()

            if recipe:
                recipe.embedding = None
                await session.commit()
                logger.info(f"Removed embedding for recipe {recipe_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error removing embedding for recipe {recipe_id}: {e}")
            return False


# Global recipe indexer instance
recipe_indexer = RecipeIndexer()
