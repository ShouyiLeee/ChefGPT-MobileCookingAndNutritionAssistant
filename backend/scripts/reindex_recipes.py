"""Script to reindex all recipes with embeddings."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.recipe import recipe_indexer
from loguru import logger


async def reindex_all():
    """Reindex all recipes."""
    logger.info("Starting recipe reindexing...")

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
            results = await recipe_indexer.reindex_all_recipes(session)

            logger.info(f"Reindexing complete:")
            logger.info(f"  Success: {results['success']}")
            logger.info(f"  Failed: {results['failed']}")
            logger.info(f"  Skipped: {results['skipped']}")

        except Exception as e:
            logger.error(f"Error during reindexing: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reindex_all())
