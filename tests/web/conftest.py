"""Web test fixtures — test app with web routers, session cookie helpers."""

from __future__ import annotations

from typing import AsyncIterator

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.auth.models import User
from app.auth.service import hash_password
from app.web.deps import create_session_token, generate_csrf_token

# Import web routers
from app.web.routes.auth import router as web_auth_router
from app.web.routes.dashboard import router as web_dashboard_router
from app.web.routes.quality import router as web_quality_router


@pytest_asyncio.fixture
async def web_client(
    _ddl_engine,
    db_session: AsyncSession,
) -> AsyncIterator[AsyncClient]:
    """Test client with web routers for HTML page tests."""
    app = FastAPI(title="test-web")

    app.include_router(web_auth_router)
    app.include_router(web_dashboard_router)
    app.include_router(web_quality_router)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=False) as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create or reuse an admin user directly in DB."""
    result = await db_session.execute(
        select(User).where(User.username == "webadmin")
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    user = User(
        username="webadmin",
        email="webadmin@test.com",
        hashed_password=hash_password("password123"),
        role="admin",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_session_cookie(admin_user: User) -> str:
    """Return a valid session cookie value for the admin user."""
    csrf = generate_csrf_token()
    return create_session_token(admin_user.id, admin_user.role, csrf)
