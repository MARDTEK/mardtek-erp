"""Tests for web auth routes — login page, form submit, logout."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
class TestLoginPage:
    """GET /login"""

    async def test_login_page_renders(self, web_client: AsyncClient):
        resp = await web_client.get("/login")
        assert resp.status_code == 200
        assert "MARDTEK" in resp.text
        assert "<form" in resp.text
        assert "_csrf" in resp.text

    async def test_login_page_has_username_field(self, web_client: AsyncClient):
        resp = await web_client.get("/login")
        assert 'name="username"' in resp.text

    async def test_login_page_has_password_field(self, web_client: AsyncClient):
        resp = await web_client.get("/login")
        assert 'name="password"' in resp.text


@pytest.mark.asyncio
class TestLoginSubmit:
    """POST /login"""

    async def test_valid_login_redirects_to_dashboard(
        self, web_client: AsyncClient, admin_user
    ):
        resp = await web_client.post("/login", data={
            "username": admin_user.username,
            "password": "password123",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["location"]

    async def test_valid_login_sets_session_cookie(
        self, web_client: AsyncClient, admin_user
    ):
        resp = await web_client.post("/login", data={
            "username": admin_user.username,
            "password": "password123",
        }, follow_redirects=False)
        assert settings.SESSION_COOKIE_NAME in resp.cookies
        cookie = resp.cookies[settings.SESSION_COOKIE_NAME]
        assert len(cookie) > 20  # signed token is long

    async def test_invalid_login_shows_error(self, web_client: AsyncClient):
        resp = await web_client.post("/login", data={
            "username": "nobody",
            "password": "wrong",
        })
        assert resp.status_code == 401
        assert "Invalid" in resp.text or "invalid" in resp.text

    async def test_invalid_login_keeps_error_page(self, web_client: AsyncClient):
        resp = await web_client.post("/login", data={
            "username": "ghost",
            "password": "bad",
        })
        assert resp.status_code == 401
        # Error page still renders login form
        assert "<form" in resp.text
        assert 'name="username"' in resp.text


@pytest.mark.asyncio
class TestLogout:
    """POST /logout"""

    async def test_logout_clears_cookie(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.post(
            "/logout",
            cookies={settings.SESSION_COOKIE_NAME: admin_session_cookie},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/login" in resp.headers["location"]
        # Cookie should be deleted (max-age=0 or empty)
        cookie_header = resp.headers.get("set-cookie", "")
        assert settings.SESSION_COOKIE_NAME in cookie_header


@pytest.mark.asyncio
class TestProtectedPages:
    """Protected pages redirect to login when no session."""

    async def test_dashboard_redirects_without_session(self, web_client: AsyncClient):
        resp = await web_client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 307
        assert "/login" in resp.headers["location"]

    async def test_dashboard_redirects_with_expired_cookie(self, web_client: AsyncClient):
        resp = await web_client.get(
            "/dashboard",
            cookies={settings.SESSION_COOKIE_NAME: "expired.garbage.token"},
            follow_redirects=False,
        )
        assert resp.status_code == 307
        assert "/login" in resp.headers["location"]

    async def test_quality_redirects_without_session(self, web_client: AsyncClient):
        resp = await web_client.get("/quality/documents", follow_redirects=False)
        assert resp.status_code == 307
        assert "/login" in resp.headers["location"]
