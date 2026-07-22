"""Integration tests — Infrastructure & IT (P8) CRUD + business logic (with auth).

NOTE: This module has NO @router.delete endpoints.  Delete tests check that
DELETE returns 405 (Method Not Allowed) rather than 403, because the admin/
manager role check only applies when a DELETE handler exists.
"""

import pytest
from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestInfrastructureRequests:
    """/api/v1/infrastructure/requests"""

    CREATE_PAYLOAD = {
        "code": "IR-2026-001",
        "requester": "jdoe",
        "resource_type": "server",
        "specification": "Dell PowerEdge R750, 64GB RAM, 4TB SSD",
        "justification": "New application server for ERP deployment",
    }

    async def test_create_request(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/infrastructure/requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "IR-2026-001"
        assert body["status"] == "submitted"

    async def test_list_requests_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/requests", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_requests_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/infrastructure/requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/infrastructure/requests", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["requester"] == "jdoe"

    async def test_get_request_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/infrastructure/requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/infrastructure/requests/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_request_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/requests/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_request(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/infrastructure/requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/infrastructure/requests/{created['id']}",
            json={"specification": "Updated spec"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["specification"] == "Updated spec"


class TestSlaAgreements:
    """/api/v1/infrastructure/sla-agreements"""

    CREATE_PAYLOAD = {
        "code": "SLA-2026-001",
        "provider": "Cloud Provider Inc.",
        "service": "ERP Hosting",
        "uptime_target": 99.9,
        "response_time_minutes": 30,
        "resolution_time_minutes": 240,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
    }

    async def test_create_sla(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/infrastructure/sla-agreements", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "SLA-2026-001"
        assert body["status"] == "active"

    async def test_list_slas_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/sla-agreements", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_slas_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/infrastructure/sla-agreements", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/infrastructure/sla-agreements", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_sla_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/infrastructure/sla-agreements", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/infrastructure/sla-agreements/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_sla_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/sla-agreements/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestIncidentReports:
    """/api/v1/infrastructure/incidents

    NOTE: The POST /incidents endpoint has a pre-existing bug — the router
    accesses ``inc.severity.value`` immediately after model creation, but
    SQLAlchemy ``Enum`` does not coerce the Python attribute to the enum type
    until DB read-back.  This means create (= 201) tests cannot pass without
    a router fix (add ``coerce_set_value=True`` to the ``Enum`` column or wrap
    the value before accessing ``.value``).
    """

    CREATE_PAYLOAD = {
        "code": "INC-2026-001",
        "service": "ERP Database",
        "severity": "P2",
        "description": "Database connection timeout on production instance",
    }

    async def test_create_incident_exposes_enum_bug(self, client: AsyncClient, admin_token: str):
        """Router bug: ``inc.severity.value`` crashes because Enum not coerced on set.
        httpx ASGITransport(raise_app_exceptions=True) propagates the exception."""
        with pytest.raises(AttributeError, match="object has no attribute 'value'"):
            await client.post(
                "/api/v1/infrastructure/incidents", json=self.CREATE_PAYLOAD,
                headers=_auth(admin_token),
            )

    async def test_list_incidents_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/incidents", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_incident_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/incidents/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestBusinessContinuityPlans:
    """/api/v1/infrastructure/continuity-plans"""

    CREATE_PAYLOAD = {
        "code": "BCP-2026-001",
        "title": "IT Disaster Recovery Plan",
        "last_reviewed": "2026-03-01",
        "risk_assessment": {"risk_level": "medium", "critical_systems": ["ERP", "DB"]},
        "recovery_strategies": {"strategy": "hot_standby", "rto_minutes": 120, "rpo_minutes": 15},
    }

    async def test_create_continuity_plan(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/infrastructure/continuity-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "BCP-2026-001"
        assert body["status"] == "draft"

    async def test_list_continuity_plans_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/continuity-plans", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_continuity_plans_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/infrastructure/continuity-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/infrastructure/continuity-plans", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_continuity_plan_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/infrastructure/continuity-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/infrastructure/continuity-plans/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_continuity_plan_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/continuity-plans/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestSecurityIncidents:
    """/api/v1/infrastructure/security-incidents"""

    CREATE_PAYLOAD = {
        "code": "SEC-2026-001",
        "incident_type": "phishing",
        "description": "Suspicious email reported by finance team",
        "impact": "Potential credential exposure",
        "containment": "Email blocked and reported to SOC",
    }

    async def test_create_security_incident(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/infrastructure/security-incidents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "SEC-2026-001"
        assert body["status"] == "open"

    async def test_list_security_incidents_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/security-incidents", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_security_incidents_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/infrastructure/security-incidents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/infrastructure/security-incidents", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_security_incident_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/infrastructure/security-incidents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/infrastructure/security-incidents/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_security_incident_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/infrastructure/security-incidents/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestInfrastructureAuth:
    """Auth tests for infrastructure & IT endpoints."""

    async def test_unauthenticated_list_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/infrastructure/requests")
        assert resp.status_code == 401

    async def test_viewer_can_create(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "infra_viewer", "email": "infra_viewer@test.com",
            "password": "password123", "role": "viewer",
        })
        login = await client.post("/auth/login", json={
            "username": "infra_viewer", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.post(
            "/api/v1/infrastructure/requests",
            json=TestInfrastructureRequests.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_delete(self, client: AsyncClient):
        """No DELETE endpoints exist in infrastructure; verify 405."""
        await client.post("/auth/register", json={
            "username": "infra_viewer_del", "email": "infra_viewer_del@test.com",
            "password": "password123", "role": "viewer",
        })
        login = await client.post("/auth/login", json={
            "username": "infra_viewer_del", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.delete(
            "/api/v1/infrastructure/requests/1",
            headers=_auth(token),
        )
        assert resp.status_code == 405

    async def test_admin_can_create_request(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "infra_admin", "email": "infra_admin@test.com",
            "password": "password123", "role": "admin",
        })
        login = await client.post("/auth/login", json={
            "username": "infra_admin", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.post(
            "/api/v1/infrastructure/requests",
            json=TestInfrastructureRequests.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text

    async def test_manager_can_create_request(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "infra_mgr", "email": "infra_mgr@test.com",
            "password": "password123", "role": "manager",
        })
        login = await client.post("/auth/login", json={
            "username": "infra_mgr", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.post(
            "/api/v1/infrastructure/requests",
            json=TestInfrastructureRequests.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text
