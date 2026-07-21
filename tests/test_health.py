"""Smoke test — health endpoint must respond."""

from httpx import AsyncClient


class TestHealth:
    async def test_health_returns_ok(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["app"] == "MARDTEK ERP"
