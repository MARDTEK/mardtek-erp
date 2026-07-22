"""Integration tests — Strategic Planning (P1) CRUD + business logic (with auth).

NOTE: This module has NO @router.delete endpoints.  Delete tests check that
DELETE returns 405 (Method Not Allowed) rather than 403, because the admin/
manager role check only applies when a DELETE handler exists.
"""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestQualityPolicies:
    """/api/v1/strategic/quality-policies"""

    CREATE_PAYLOAD = {
        "code": "POL-P1-001",
        "title": "Quality Policy 2026",
        "content": "We commit to excellence through continuous improvement.",
    }

    async def test_create_quality_policy(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/strategic/quality-policies", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "POL-P1-001"
        assert body["status"] == "draft"

    async def test_list_quality_policies_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/strategic/quality-policies", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_quality_policies_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/strategic/quality-policies", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/strategic/quality-policies", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Quality Policy 2026"

    async def test_get_quality_policy_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/strategic/quality-policies", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/strategic/quality-policies/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_quality_policy_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/strategic/quality-policies/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_approve_quality_policy(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/strategic/quality-policies", json={
                **self.CREATE_PAYLOAD, "code": "POL-P1-002",
            },
            headers=_auth(admin_token),
        )).json()
        resp = await client.post(
            f"/api/v1/strategic/quality-policies/{created['id']}/approve",
            json={"approved_by": "ceo"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"
        assert resp.json()["approved_by"] == "ceo"


class TestQualityObjectives:
    """/api/v1/strategic/quality-objectives"""

    CREATE_PAYLOAD = {
        "code": "MAT-P1-001",
        "objective": "Reduce defect rate by 15%",
        "process_code": "P2",
        "target_value": 85.0,
        "metric_unit": "percent",
        "year": 2026,
        "responsible": "qa_manager",
    }

    async def test_create_quality_objective(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/strategic/quality-objectives", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "MAT-P1-001"
        assert body["status"] == "on_track"

    async def test_list_quality_objectives_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/strategic/quality-objectives", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_quality_objectives_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/strategic/quality-objectives", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/strategic/quality-objectives", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_quality_objective_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/strategic/quality-objectives", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/strategic/quality-objectives/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_quality_objective_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/strategic/quality-objectives/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_progress(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/strategic/quality-objectives", json={
                **self.CREATE_PAYLOAD, "code": "MAT-P1-002",
            },
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/strategic/quality-objectives/{created['id']}/progress",
            json={"actual_value": 90.0},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["actual_value"] == 90.0
        assert resp.json()["status"] == "achieved"


class TestMarketingPlans:
    """/api/v1/strategic/marketing-plans"""

    CREATE_PAYLOAD = {
        "code": "PLN-P1-001",
        "title": "Marketing Plan 2026",
        "year": 2026,
        "goals": "Increase market share by 10%",
        "budget": 50000.00,
    }

    async def test_create_marketing_plan(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/strategic/marketing-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "PLN-P1-001"
        assert body["status"] == "draft"

    async def test_list_marketing_plans_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/strategic/marketing-plans", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_marketing_plans_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/strategic/marketing-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/strategic/marketing-plans", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_marketing_plan_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/strategic/marketing-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/strategic/marketing-plans/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_marketing_plan_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/strategic/marketing-plans/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestManagementReviews:
    """/api/v1/strategic/management-reviews"""

    CREATE_PAYLOAD = {
        "code": "INF-P1-001",
        "title": "Q1 2026 Management Review",
        "review_period_start": "2026-01-01",
        "review_period_end": "2026-03-31",
        "prepared_by": "quality_rep",
        "summary": "All QMS processes performing as expected.",
    }

    async def test_create_management_review(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/strategic/management-reviews", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "INF-P1-001"

    async def test_list_management_reviews_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/strategic/management-reviews", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_management_reviews_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/strategic/management-reviews", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/strategic/management-reviews", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_management_review_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/strategic/management-reviews/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestQmsScope:
    """/api/v1/strategic/qms-scope — singleton-like (only one active)."""

    CREATE_PAYLOAD = {
        "scope_description": "ISO 9001:2015 Quality Management System",
        "applicable_normative": "ISO 9001:2015",
    }

    async def test_get_qms_scope_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/strategic/qms-scope", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_create_qms_scope(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/strategic/qms-scope", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["is_current"] is True

    async def test_get_qms_scope_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/strategic/qms-scope", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/strategic/qms-scope", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["applicable_normative"] == "ISO 9001:2015"

    async def test_create_replaces_previous_scope(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/strategic/qms-scope", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.post(
            "/api/v1/strategic/qms-scope", json={
                "scope_description": "Updated scope",
                "applicable_normative": "ISO 14001:2015",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        assert resp.json()["is_current"] is True
        assert resp.json()["applicable_normative"] == "ISO 14001:2015"


class TestStrategicPlanningAuth:
    """Auth tests for strategic planning endpoints."""

    async def test_unauthenticated_list_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/strategic/quality-policies")
        assert resp.status_code == 401

    async def test_viewer_can_create(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "sp_viewer", "email": "sp_viewer@test.com",
            "password": "password123", "role": "viewer",
        })
        login = await client.post("/auth/login", json={
            "username": "sp_viewer", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.post(
            "/api/v1/strategic/quality-policies",
            json=TestQualityPolicies.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 201

    async def test_viewer_cannot_delete(self, client: AsyncClient):
        """No DELETE endpoints exist in strategic planning; verify 405."""
        await client.post("/auth/register", json={
            "username": "sp_viewer_del", "email": "sp_viewer_del@test.com",
            "password": "password123", "role": "viewer",
        })
        login = await client.post("/auth/login", json={
            "username": "sp_viewer_del", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.delete(
            "/api/v1/strategic/quality-policies/1",
            headers=_auth(token),
        )
        assert resp.status_code == 405

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

    async def test_viewer_cannot_approve_policy(self, client: AsyncClient):
        admin_token = await self._register_and_login(client, "sp_admin_app", "admin")
        viewer_token = await self._register_and_login(client, "sp_viewer_app", "viewer")

        create = await client.post(
            "/api/v1/strategic/quality-policies",
            json=TestQualityPolicies.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert create.status_code == 201, create.text
        policy_id = create.json()["id"]

        resp = await client.post(
            f"/api/v1/strategic/quality-policies/{policy_id}/approve",
            json={"approved_by": "viewer"},
            headers=_auth(viewer_token),
        )
        assert resp.status_code == 403

    async def test_admin_can_approve_policy(self, client: AsyncClient):
        token = await self._register_and_login(client, "sp_admin_ap2", "admin")

        create = await client.post(
            "/api/v1/strategic/quality-policies",
            json=TestQualityPolicies.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert create.status_code == 201, create.text
        policy_id = create.json()["id"]

        resp = await client.post(
            f"/api/v1/strategic/quality-policies/{policy_id}/approve",
            json={"approved_by": "admin"},
            headers=_auth(token),
        )
        assert resp.status_code == 200

    async def test_manager_can_approve_policy(self, client: AsyncClient):
        token = await self._register_and_login(client, "sp_mgr_ap1", "manager")

        create = await client.post(
            "/api/v1/strategic/quality-policies",
            json=TestQualityPolicies.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert create.status_code == 201, create.text
        policy_id = create.json()["id"]

        resp = await client.post(
            f"/api/v1/strategic/quality-policies/{policy_id}/approve",
            json={"approved_by": "manager"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
