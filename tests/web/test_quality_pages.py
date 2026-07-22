"""Tests for quality management web pages — list, detail, HTMX partials."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import settings


def _auth_cookie(cookie: str) -> dict:
    return {settings.SESSION_COOKIE_NAME: cookie}


@pytest.mark.asyncio
class TestQualityDocumentsList:
    """GET /quality/documents"""

    async def test_list_renders(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/documents",
            cookies=_auth_cookie(admin_session_cookie),
        )
        assert resp.status_code == 200
        assert "Documents" in resp.text

    async def test_list_has_create_button(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/documents",
            cookies=_auth_cookie(admin_session_cookie),
        )
        assert "New" in resp.text or "Create" in resp.text or "+" in resp.text

    async def test_list_has_search_form(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/documents",
            cookies=_auth_cookie(admin_session_cookie),
        )
        assert "search" in resp.text.lower() or "Search" in resp.text

    async def test_list_shows_table_structure(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/documents",
            cookies=_auth_cookie(admin_session_cookie),
        )
        # Table should have header columns
        assert "Code" in resp.text or "code" in resp.text
        assert "Title" in resp.text or "title" in resp.text


@pytest.mark.asyncio
class TestQualityDocumentsHTMXPartial:
    """GET /quality/documents/table (HTMX partial)"""

    async def test_table_partial_returns_fragment(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/documents/table",
            headers={"HX-Request": "true"},
            cookies=_auth_cookie(admin_session_cookie),
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestQualityDocumentsDetail:
    """GET /quality/documents/{id}"""

    async def test_detail_404_for_missing(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/documents/99999",
            cookies=_auth_cookie(admin_session_cookie),
            follow_redirects=False,
        )
        assert resp.status_code in (404, 303, 307)


@pytest.mark.asyncio
class TestQualityNonConformitiesList:
    """GET /quality/non-conformities"""

    async def test_list_renders(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/non-conformities",
            cookies=_auth_cookie(admin_session_cookie),
        )
        assert resp.status_code == 200
        assert "Non-Conformities" in resp.text or "Non-conformities" in resp.text


@pytest.mark.asyncio
class TestQualityCorrectiveActionsList:
    """GET /quality/corrective-actions"""

    async def test_list_renders(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/corrective-actions",
            cookies=_auth_cookie(admin_session_cookie),
        )
        assert resp.status_code == 200
        assert "Corrective" in resp.text


@pytest.mark.asyncio
class TestQualityAuditsList:
    """GET /quality/audits"""

    async def test_list_renders(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/audits",
            cookies=_auth_cookie(admin_session_cookie),
        )
        assert resp.status_code == 200
        assert "Audit" in resp.text


@pytest.mark.asyncio
class TestQualityImprovementsList:
    """GET /quality/improvements"""

    async def test_list_renders(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality/improvements",
            cookies=_auth_cookie(admin_session_cookie),
        )
        assert resp.status_code == 200
        assert "Improvement" in resp.text


@pytest.mark.asyncio
class TestQualityRootRedirect:
    """GET /quality"""

    async def test_quality_root_redirects(
        self, web_client: AsyncClient, admin_session_cookie
    ):
        resp = await web_client.get(
            "/quality",
            cookies=_auth_cookie(admin_session_cookie),
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert "/quality/documents" in resp.headers["location"]
