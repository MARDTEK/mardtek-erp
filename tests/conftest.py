"""Test fixtures — isolated test database, async client, per-request sessions.

Uses a sync engine for DDL (create_all / drop_all) to avoid greenlet/event-loop
conflicts with pytest-asyncio session-scoped fixtures.  The async engine is
used only during actual test execution.
"""

from __future__ import annotations

from typing import AsyncIterator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.database import Base, get_db

# Import ALL models so Base.metadata is populated before DDL
from app.modules.quality_management.domain import models as _qm_models      # noqa: F401
from app.modules.commercial_sales.domain import models as _cs_models        # noqa: F401
from app.modules.pmo_projects.domain import models as _pmo_models           # noqa: F401
from app.modules.training_services.domain import models as _train_models    # noqa: F401
from app.modules.strategic_planning.domain import models as _sp_models      # noqa: F401
from app.modules.tech_development.domain import models as _td_models        # noqa: F401
from app.modules.procurement.domain import models as _proc_models           # noqa: F401
from app.modules.analytics_performance.domain import models as _ap_models   # noqa: F401
from app.modules.customer_experience.domain import models as _cx_models     # noqa: F401
from app.modules.infrastructure_it.domain import models as _infra_models    # noqa: F401
from app.modules.human_resources.domain import models as _hr_models         # noqa: F401
from app.auth import models as _auth_models                                 # noqa: F401

# ── Test settings ──────────────────────────────────────────────────────────

test_settings = Settings(_env_file=None)
TEST_DB_URL = test_settings.TEST_DATABASE_URL


# ── Sync engine for DDL (create / drop tables) ─────────────────────────────

def _sync_db_url(async_url: str) -> str:
    """Convert asyncpg URL to psycopg2 URL for sync engine."""
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


def _drop_all_enums(engine):
    """Drop all ENUM types in the public schema to avoid collisions across sessions."""
    with engine.connect() as conn:
        conn.execute(text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN SELECT typname FROM pg_type
                    WHERE typtype = 'e'
                      AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                LOOP
                    EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        conn.commit()


@pytest.fixture(scope="session")
def _ddl_engine():
    """Sync engine used once per session to create / drop tables."""
    sync_url = _sync_db_url(TEST_DB_URL)
    engine = create_engine(sync_url, echo=False)
    _drop_all_enums(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest_asyncio.fixture
async def db_session(_ddl_engine) -> AsyncIterator[AsyncSession]:
    """Fresh engine + session per test — no shared pool, no loop conflicts."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
    await engine.dispose()


# ── HTTP test client ───────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncIterator[AsyncClient]:
    """Lightweight test client — no production lifespan, no production engine."""

    # Build a minimal test app with the same routers but NO lifespan
    app = FastAPI(title="test")

    from app.auth.router import router as auth_router
    from app.modules.quality_management.router import router as quality_router
    from app.modules.commercial_sales.router import router as commercial_router
    from app.modules.pmo_projects.router import router as pmo_projects_router
    from app.modules.training_services.router import router as training_router
    from app.modules.strategic_planning.router import router as strategic_router
    from app.modules.tech_development.router import router as tech_router
    from app.modules.procurement.router import router as procurement_router
    from app.modules.analytics_performance.router import router as analytics_router
    from app.modules.customer_experience.router import router as customer_router
    from app.modules.infrastructure_it.router import router as infra_router
    from app.modules.human_resources.router import router as hr_router

    app.include_router(auth_router)
    app.include_router(quality_router, prefix="/api/v1/quality")
    app.include_router(commercial_router, prefix="/api/v1/commercial")
    app.include_router(pmo_projects_router, prefix="/api/v1/projects")
    app.include_router(training_router, prefix="/api/v1/training")
    app.include_router(strategic_router, prefix="/api/v1/strategic")
    app.include_router(tech_router, prefix="/api/v1/development")
    app.include_router(procurement_router, prefix="/api/v1/procurement")
    app.include_router(analytics_router, prefix="/api/v1/analytics")
    app.include_router(customer_router, prefix="/api/v1/customer-satisfaction")
    app.include_router(infra_router, prefix="/api/v1/infrastructure")
    app.include_router(hr_router, prefix="/api/v1/hr")

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": test_settings.APP_NAME}

    # Override the dependency with our test session
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    """Register an admin user and return a valid JWT token."""
    await client.post("/auth/register", json={
        "username": "admin",
        "email": "admin@test.com",
        "password": "password123",
        "role": "admin",
    })
    resp = await client.post("/auth/login", json={
        "username": "admin",
        "password": "password123",
    })
    return resp.json()["access_token"]
