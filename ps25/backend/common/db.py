"""Database connection and session management.

Implements:
  - Async SQLAlchemy engine with psycopg3
  - Session factory for dependency injection
  - Sync engine + create_tables() for schema creation (SSOT 02 §6.1, SSOT 09 §34.3)

No Alembic is used. Schema is created via SQLAlchemy.metadata.create_all().
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from common.config import settings

# ---------------------------------------------------------------------------
# Async engine (used by FastAPI routes)
# ---------------------------------------------------------------------------
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async session factory — injected into routes via dependency
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ---------------------------------------------------------------------------
# Sync engine (used for create_tables / startup schema creation)
# ---------------------------------------------------------------------------
sync_engine = create_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
)

# Sync session factory (used for setup/seed scripts)
sync_session_factory = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Base model — all SQLAlchemy models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy models.

    The metadata bound to this base contains all tables defined in
    common/models.py and any module-level model definitions.
    """

    pass


# ---------------------------------------------------------------------------
# Dependency: async session
# ---------------------------------------------------------------------------
async def get_async_session() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        yield session


# Dependency: sync session (for setup/migration scripts)
def get_sync_session() -> sessionmaker:
    """Returns the sync session factory."""
    return sync_session_factory


# ---------------------------------------------------------------------------
# Schema creation: SQLAlchemy.metadata.create_all() — NO Alembic
# ---------------------------------------------------------------------------
def create_tables():
    """Create all tables in the database via SQLAlchemy.metadata.create_all().

    Imports all models first to ensure they are registered on the Base metadata.
    Then executes CREATE TABLE IF NOT EXISTS for every model.

    SSOT 02 §6.1: 'Schema created through SQLAlchemy.metadata.create_all().'
    SSOT 09 §34.3: 'Do not introduce Alembic.'
    """
    # Import models here to ensure they are registered on Base.metadata
    import common.models  # noqa: F401

    # Create all tables — no Alembic, pure SQLAlchemy
    Base.metadata.create_all(bind=sync_engine)


# ---------------------------------------------------------------------------
# Async context manager for startup
# ---------------------------------------------------------------------------
async def close_db():
    """Close the async engine connection pool."""
    await async_engine.dispose()


# Engine reference for direct use (tests, scripts)
engine = async_engine