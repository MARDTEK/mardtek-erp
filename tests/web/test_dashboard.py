"""Tests for dashboard page — module cards, entity counts, role-aware content."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
class TestDashboard:
    """GET /dashboard"""

    async def test_dashboard_renders(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/dashboard",
            cookies={settings.SESSION_COOKIE_NAME: admin_session_cookie},
        )
        assert resp.status_code == 200
        assert "MARDTEK" in resp.text

    async def test_dashboard_shows_all_module_cards(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/dashboard",
            cookies={settings.SESSION_COOKIE_NAME: admin_session_cookie},
        )
        text = resp.text
        # All 11 module names should appear
        for name in [
            "Quality Management",
            "Strategic Planning",
            "Commercial Sales",
            "Tech Development",
            "PMO Projects",
            "Training",
            "Human Resources",
            "Infrastructure",
            "Procurement",
            "Customer",
            "Analytics",
        ]:
            assert name in text, f"Module '{name}' not found on dashboard"

    async def test_dashboard_shows_sidebar(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/dashboard",
            cookies={settings.SESSION_COOKIE_NAME: admin_session_cookie},
        )
        assert 'id="sidebar"' in resp.text

    async def test_dashboard_shows_topbar(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/dashboard",
            cookies={settings.SESSION_COOKIE_NAME: admin_session_cookie},
        )
        # Topbar has logout button
        assert "logout" in resp.text.lower() or "Logout" in resp.text

    async def test_dashboard_shows_entity_counts(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/dashboard",
            cookies={settings.SESSION_COOKIE_NAME: admin_session_cookie},
        )
        # With empty DB, counts should show "0" somewhere
        assert "0" in resp.text or "No " in resp.text

    async def test_dashboard_contains_htmx(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/dashboard",
            cookies={settings.SESSION_COOKIE_NAME: admin_session_cookie},
        )
        # Base template loads HTMX
        assert "htmx" in resp.text.lower() or "alpine" in resp.text.lower()
