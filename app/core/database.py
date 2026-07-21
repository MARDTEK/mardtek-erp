"""Database engine, session, and Base — engine is lazy, created on first use."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Lazy engine — created on first async use, NOT at import time ──────────

_engine: AsyncEngine | None = None
_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the singleton production engine, creating it lazily."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL, echo=settings.DEBUG
        )
    return _engine


def async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return a session factory bound to the lazy engine."""
    global _factory
    if _factory is None:
        _factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _factory


async def dispose_engine() -> None:
    """Dispose the engine pool (call during app shutdown)."""
    global _engine, _factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _factory = None


# ── Declarative base ─────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


# ── Session dependency ───────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a session, commits on success,
    rolls back on error, and always closes."""
    factory = async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
