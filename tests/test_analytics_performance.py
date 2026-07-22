"""Integration tests — Analytics & Performance CRUD (with auth)."""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestIndicators:
    """/api/v1/analytics/indicators"""

    CREATE_PAYLOAD = {
        "code": "KPI-P4-001",
        "name": "Sprint Velocity",
        "process_code": "P4",
    }

    async def test_create_indicator(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/analytics/indicators", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["code"] == "KPI-P4-001"
        assert resp.json()["is_active"] is True

    async def test_list_indicators_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/analytics/indicators", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_indicators_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/analytics/indicators", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/analytics/indicators", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Sprint Velocity"

    async def test_get_indicator_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/analytics/indicators", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/analytics/indicators/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_indicator_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/analytics/indicators/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_delete_indicator(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/analytics/indicators", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/analytics/indicators/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 204

        get_resp = await client.get(
            f"/api/v1/analytics/indicators/{created['id']}",
            headers=_auth(admin_token),
        )
        assert get_resp.status_code == 404


class TestDataRecords:
    """/api/v1/analytics/indicators/{id}/record + /records"""

    async def test_submit_data_record(self, client: AsyncClient, admin_token: str):
        indicator = (await client.post(
            "/api/v1/analytics/indicators",
            json={"code": "KPI-P4-010", "name": "Defect Rate", "process_code": "P4"},
            headers=_auth(admin_token),
        )).json()

        resp = await client.post(
            f"/api/v1/analytics/indicators/{indicator['id']}/record",
            json={"period": "2026-01", "value": 95.5, "recorded_by": "jdoe"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["value"] == 95.5

    async def test_list_data_records(self, client: AsyncClient, admin_token: str):
        indicator = (await client.post(
            "/api/v1/analytics/indicators",
            json={"code": "KPI-P4-011", "name": "Uptime", "process_code": "P4"},
            headers=_auth(admin_token),
        )).json()

        await client.post(
            f"/api/v1/analytics/indicators/{indicator['id']}/record",
            json={"period": "2026-01", "value": 99.9, "recorded_by": "jdoe"},
            headers=_auth(admin_token),
        )

        resp = await client.get(
            f"/api/v1/analytics/indicators/{indicator['id']}/records",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_submit_data_record_nonexistent_indicator(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/analytics/indicators/99999/record",
            json={"period": "2026-01", "value": 50.0, "recorded_by": "jdoe"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestDashboards:
    """/api/v1/analytics/dashboards"""

    CREATE_PAYLOAD = {
        "code": "DASH-EXEC-001",
        "title": "Executive Dashboard",
    }

    async def test_create_dashboard(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/analytics/dashboards", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["code"] == "DASH-EXEC-001"

    async def test_list_dashboards_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/analytics/dashboards", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_dashboards_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/analytics/dashboards", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/analytics/dashboards", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_dashboard_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/analytics/dashboards", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/analytics/dashboards/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_dashboard_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/analytics/dashboards/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_delete_dashboard(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/analytics/dashboards", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/analytics/dashboards/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 204


class TestTrendAnalysisReports:
    """/api/v1/analytics/trend-reports"""

    async def test_create_trend_report(self, client: AsyncClient, admin_token: str):
        indicator = (await client.post(
            "/api/v1/analytics/indicators",
            json={"code": "KPI-P4-020", "name": "Test Trend", "process_code": "P4"},
            headers=_auth(admin_token),
        )).json()

        resp = await client.post(
            "/api/v1/analytics/trend-reports",
            json={
                "code": "TREND-001",
                "indicator_id": indicator["id"],
                "period_start": "2026-01-01",
                "period_end": "2026-06-30",
                "trend": "up",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["trend"] == "up"

    async def test_list_trend_reports_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/analytics/trend-reports", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_trend_reports_after_create(self, client: AsyncClient, admin_token: str):
        indicator = (await client.post(
            "/api/v1/analytics/indicators",
            json={"code": "KPI-P4-021", "name": "List Trend", "process_code": "P4"},
            headers=_auth(admin_token),
        )).json()
        await client.post(
            "/api/v1/analytics/trend-reports",
            json={
                "code": "TREND-002",
                "indicator_id": indicator["id"],
                "period_start": "2026-01-01",
                "period_end": "2026-06-30",
                "trend": "flat",
            },
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/analytics/trend-reports", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_trend_report_by_id(self, client: AsyncClient, admin_token: str):
        indicator = (await client.post(
            "/api/v1/analytics/indicators",
            json={"code": "KPI-P4-022", "name": "Get Trend", "process_code": "P4"},
            headers=_auth(admin_token),
        )).json()
        created = (await client.post(
            "/api/v1/analytics/trend-reports",
            json={
                "code": "TREND-003",
                "indicator_id": indicator["id"],
                "period_start": "2026-01-01",
                "period_end": "2026-06-30",
                "trend": "down",
            },
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/analytics/trend-reports/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_trend_report_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/analytics/trend-reports/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestKpiReports:
    """/api/v1/analytics/kpi-reports"""

    CREATE_PAYLOAD = {
        "code": "KPI-RPT-001",
        "title": "Monthly KPI Summary",
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
    }

    async def test_create_kpi_report(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/analytics/kpi-reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["code"] == "KPI-RPT-001"

    async def test_list_kpi_reports_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/analytics/kpi-reports", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_kpi_reports_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/analytics/kpi-reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/analytics/kpi-reports", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_kpi_report_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/analytics/kpi-reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/analytics/kpi-reports/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_kpi_report_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/analytics/kpi-reports/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestAnalyticsAuth:
    """Auth guard tests for /api/v1/analytics/*"""

    async def _register_and_login(self, client: AsyncClient, username: str, role: str) -> str:
        await client.post("/auth/register", json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "password123",
            "role": role,
        })
        resp = await client.post("/auth/login", json={
            "username": username,
            "password": "password123",
        })
        return resp.json()["access_token"]

    async def test_unauthenticated_request_blocked(self, client: AsyncClient):
        """No token → 401 for GET list."""
        resp = await client.get("/api/v1/analytics/indicators")
        assert resp.status_code == 401

    async def test_viewer_cannot_delete(self, client: AsyncClient):
        """Viewer role must be forbidden from DELETE on indicators."""
        token = await self._register_and_login(client, "vieweranalytics", "viewer")

        create = await client.post(
            "/api/v1/analytics/indicators",
            json={
                "code": "KPI-P4-999",
                "name": "Delete Test Indicator",
                "process_code": "P4",
            },
            headers=_auth(token),
        )
        assert create.status_code == 201, create.text
        ind_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/analytics/indicators/{ind_id}",
            headers=_auth(token),
        )
        assert resp.status_code == 403
        assert "not allowed" in resp.text

    async def test_viewer_can_create(self, client: AsyncClient):
        """Viewer role must be allowed to POST (create)."""
        token = await self._register_and_login(client, "vieweranalytics2", "viewer")

        resp = await client.post(
            "/api/v1/analytics/indicators",
            json={
                "code": "KPI-P4-998",
                "name": "Viewer Indicator",
                "process_code": "P4",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["name"] == "Viewer Indicator"
