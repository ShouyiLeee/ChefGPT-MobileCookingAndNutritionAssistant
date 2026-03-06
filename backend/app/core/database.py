"""Database connection and session management."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

# ── URL helpers ──────────────────────────────────────────────────────────────
_db_url = settings.database_url
_is_sqlite = _db_url.startswith("sqlite")

# Sync URL (used by Alembic + create_db_and_tables)
_sync_url = _db_url

# Async URL
if _is_sqlite:
    _async_url = _db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
else:
    _async_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# ── Engines ───────────────────────────────────────────────────────────────────
# SQLite doesn't support pool_size / max_overflow
_engine_kwargs: dict = {"echo": settings.debug}
if not _is_sqlite:
    _engine_kwargs["pool_pre_ping"] = True

sync_engine = create_engine(_sync_url, **_engine_kwargs)
async_engine = create_async_engine(_async_url, **_engine_kwargs)

# ── Session factory ───────────────────────────────────────────────────────────
async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def create_db_and_tables() -> None:
    """Create all database tables (called at startup)."""
    SQLModel.metadata.create_all(sync_engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Session:
    """Return a sync session (for Alembic migrations)."""
    return Session(sync_engine)
