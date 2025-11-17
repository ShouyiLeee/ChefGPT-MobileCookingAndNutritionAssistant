"""Script to seed database with sample recipes and generate embeddings."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.recipe import Recipe, Ingredient
from app.services.recipe import recipe_indexer
from loguru import logger


# Sample Vietnamese recipes
SAMPLE_RECIPES = [
    {
        "title": "Phở Bò (Vietnamese Beef Noodle Soup)",
        "description": "Traditional Vietnamese beef noodle soup with aromatic broth, rice noodles, and tender beef slices. A classic comfort food loved throughout Vietnam.",
        "cuisine": "vietnamese",
        "difficulty": "medium",
        "prep_time": 30,
        "cook_time": 180,
        "servings": 4,
        "category": "lunch",
        "tags": "soup,beef,noodles,traditional",
        "is_public": True,
    },
    {
        "title": "Bánh Mì Thịt (Vietnamese Sandwich)",
        "description": "Crispy baguette filled with savory pork, pickled vegetables, cilantro, and pate. A perfect fusion of French and Vietnamese cuisine.",
        "cuisine": "vietnamese",
        "difficulty": "easy",
        "prep_time": 20,
        "cook_time": 10,
        "servings": 2,
        "category": "breakfast",
        "tags": "sandwich,pork,quick,street-food",
        "is_public": True,
    },
    {
        "title": "Gỏi Cuốn (Fresh Spring Rolls)",
        "description": "Light and healthy rice paper rolls filled with shrimp, vermicelli, herbs, and vegetables. Served with peanut dipping sauce.",
        "cuisine": "vietnamese",
        "difficulty": "easy",
        "prep_time": 30,
        "cook_time": 0,
        "servings": 4,
        "category": "appetizer",
        "tags": "healthy,no-cook,vegetarian-option,fresh",
        "is_public": True,
    },
    {
        "title": "Bún Chả (Grilled Pork with Noodles)",
        "description": "Grilled pork patties and slices served with rice vermicelli, fresh herbs, and sweet-sour dipping sauce. A Hanoi specialty.",
        "cuisine": "vietnamese",
        "difficulty": "medium",
        "prep_time": 45,
        "cook_time": 20,
        "servings": 4,
        "category": "lunch",
        "tags": "pork,grilled,noodles,hanoi",
        "is_public": True,
    },
    {
        "title": "Cơm Tấm (Broken Rice with Grilled Pork)",
        "description": "Broken rice served with grilled marinated pork chop, pickled vegetables, and fish sauce. A Southern Vietnamese favorite.",
        "cuisine": "vietnamese",
        "difficulty": "easy",
        "prep_time": 15,
        "cook_time": 20,
        "servings": 2,
        "category": "dinner",
        "tags": "rice,pork,grilled,southern",
        "is_public": True,
    },
    {
        "title": "Canh Chua (Vietnamese Sour Soup)",
        "description": "Sweet and sour soup with fish, pineapple, tomatoes, and herbs. Perfectly balanced flavors in a light broth.",
        "cuisine": "vietnamese",
        "difficulty": "easy",
        "prep_time": 15,
        "cook_time": 25,
        "servings": 4,
        "category": "soup",
        "tags": "soup,fish,healthy,sour",
        "is_public": True,
    },
    {
        "title": "Chả Giò (Vietnamese Fried Spring Rolls)",
        "description": "Crispy fried rolls filled with ground pork, vegetables, and glass noodles. A popular appetizer or side dish.",
        "cuisine": "vietnamese",
        "difficulty": "medium",
        "prep_time": 40,
        "cook_time": 20,
        "servings": 6,
        "category": "appetizer",
        "tags": "fried,pork,crispy,party-food",
        "is_public": True,
    },
    {
        "title": "Cà Ri Gà (Vietnamese Chicken Curry)",
        "description": "Aromatic curry with tender chicken, potatoes, and carrots in coconut milk. Served with bread or rice.",
        "cuisine": "vietnamese",
        "difficulty": "easy",
        "prep_time": 20,
        "cook_time": 40,
        "servings": 4,
        "category": "dinner",
        "tags": "curry,chicken,coconut,comfort-food",
        "is_public": True,
    },
    {
        "title": "Xôi Gà (Sticky Rice with Chicken)",
        "description": "Savory sticky rice topped with shredded chicken, fried shallots, and herbs. A hearty breakfast dish.",
        "cuisine": "vietnamese",
        "difficulty": "medium",
        "prep_time": 30,
        "cook_time": 45,
        "servings": 4,
        "category": "breakfast",
        "tags": "rice,chicken,sticky-rice,hearty",
        "is_public": True,
    },
    {
        "title": "Mì Quảng (Quang Style Noodles)",
        "description": "Yellow noodles with shrimp, pork, and peanuts in a flavorful broth. A Central Vietnamese specialty.",
        "cuisine": "vietnamese",
        "difficulty": "medium",
        "prep_time": 30,
        "cook_time": 30,
        "servings": 4,
        "category": "lunch",
        "tags": "noodles,shrimp,pork,central",
        "is_public": True,
    },
]


async def seed_recipes():
    """Seed database with sample recipes."""
    logger.info("Starting recipe seeding...")

    # Create async engine
    async_database_url = settings.database_url.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(async_database_url, echo=False)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Create recipes
            recipes_created = []

            for recipe_data in SAMPLE_RECIPES:
                # Calculate total time
                total_time = recipe_data["prep_time"] + recipe_data["cook_time"]

                recipe = Recipe(
                    **recipe_data,
                    total_time=total_time,
                )

                session.add(recipe)
                recipes_created.append(recipe)

            await session.commit()
            logger.info(f"Created {len(recipes_created)} recipes")

            # Refresh to get IDs
            for recipe in recipes_created:
                await session.refresh(recipe)

            # Generate embeddings
            logger.info("Generating embeddings for recipes...")
            recipe_ids = [recipe.id for recipe in recipes_created]

            results = await recipe_indexer.index_recipes_batch(recipe_ids, session)

            logger.info(f"Indexing results: {results}")
            logger.info("✅ Recipe seeding completed successfully!")

        except Exception as e:
            logger.error(f"Error seeding recipes: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_recipes())
