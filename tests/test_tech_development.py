"""Integration tests — Tech Development (P4) CRUD (with auth)."""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProductRoadmaps:
    """/api/v1/development/roadmaps"""

    CREATE_PAYLOAD = {
        "code": "PLN-P4-001",
        "title": "MicroSmart 2026 Roadmap",
        "product_line": "SAAS",
        "year": 2026,
        "vision": "Market leader in ERP",
        "strategic_goals": "Expand module coverage",
    }

    async def test_create_roadmap(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/development/roadmaps", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["code"] == "PLN-P4-001"
        assert resp.json()["status"] == "draft"

    async def test_list_roadmaps_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/roadmaps", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_roadmaps_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/development/roadmaps", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/development/roadmaps", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "MicroSmart 2026 Roadmap"

    async def test_get_roadmap_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/roadmaps", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/development/roadmaps/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_roadmap_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/roadmaps/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_delete_roadmap(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/roadmaps", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/development/roadmaps/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200

        get_resp = await client.get(
            f"/api/v1/development/roadmaps/{created['id']}",
            headers=_auth(admin_token),
        )
        assert get_resp.status_code == 404


class TestReleasePlans:
    """/api/v1/development/releases"""

    CREATE_PAYLOAD = {
        "code": "PLN-P4-010",
        "title": "Q4 2026 Release",
        "version": "2.0.0",
        "product": "MicroSmart",
        "planned_date": "2026-12-01",
    }

    async def test_create_release(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/development/releases", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["title"] == "Q4 2026 Release"
        assert resp.json()["status"] == "planned"

    async def test_list_releases_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/releases", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_releases_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/development/releases", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/development/releases", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["version"] == "2.0.0"

    async def test_get_release_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/releases", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/development/releases/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_release_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/releases/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_delete_release(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/releases", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/development/releases/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200


class TestTechnicalSpecifications:
    """/api/v1/development/specifications"""

    CREATE_PAYLOAD = {
        "code": "TECH-SPEC-001",
        "title": "Authentication Module Spec",
        "content": "JWT-based auth with refresh tokens",
    }

    async def test_create_specification(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/development/specifications", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["title"] == "Authentication Module Spec"

    async def test_list_specifications_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/specifications", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_specifications_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/development/specifications", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/development/specifications", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_specification_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/specifications", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/development/specifications/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_specification_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/specifications/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_delete_specification(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/specifications", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/development/specifications/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200


class TestRiskMatrices:
    """/api/v1/development/risk-matrices"""

    CREATE_PAYLOAD = {
        "code": "MAT-P4-001",
    }

    async def test_create_risk_matrix(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/development/risk-matrices", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["code"] == "MAT-P4-001"
        assert resp.json()["version"] == "1.0"

    async def test_list_risk_matrices_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/risk-matrices", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_risk_matrices_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/development/risk-matrices", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/development/risk-matrices", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_risk_matrix_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/risk-matrices", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/development/risk-matrices/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_risk_matrix_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/risk-matrices/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_delete_risk_matrix(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/risk-matrices", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/development/risk-matrices/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200


class TestQATestReports:
    """/api/v1/development/qa-reports"""

    CREATE_PAYLOAD = {
        "code": "INF-P4-001",
        "title": "Sprint 12 QA Report",
        "test_type": "unit",
        "total_tests": 100,
        "passed": 95,
        "failed": 5,
    }

    async def test_create_qa_report(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/development/qa-reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "INF-P4-001"
        assert body["status"] == "draft"

    async def test_list_qa_reports_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/qa-reports", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_qa_reports_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/development/qa-reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/development/qa-reports", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_qa_report_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/qa-reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/development/qa-reports/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_qa_report_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/qa-reports/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_delete_qa_report(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/qa-reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/development/qa-reports/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200


class TestDeploymentRecords:
    """/api/v1/development/deployments (no DELETE endpoint)"""

    CREATE_PAYLOAD = {
        "code": "REG-P4-001",
        "environment": "staging",
        "deployed_by": "jdoe",
    }

    async def test_create_deployment(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/development/deployments", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["environment"] == "staging"

    async def test_list_deployments_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/deployments", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_deployments_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/development/deployments", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/development/deployments", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_deployment_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/deployments", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/development/deployments/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_deployment_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/deployments/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestUATSignOffs:
    """/api/v1/development/uat-signoffs"""

    CREATE_PAYLOAD = {
        "code": "FO-P4-001",
        "signed_by": "jdoe",
    }

    async def test_create_uat_signoff(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/development/uat-signoffs", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["code"] == "FO-P4-001"
        assert resp.json()["status"] == "pending"

    async def test_list_uat_signoffs_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/uat-signoffs", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_uat_signoffs_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/development/uat-signoffs", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/development/uat-signoffs", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_uat_signoff_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/uat-signoffs", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/development/uat-signoffs/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_uat_signoff_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/uat-signoffs/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_delete_uat_signoff(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/uat-signoffs", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/development/uat-signoffs/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200


class TestSolutionSunsets:
    """/api/v1/development/sunsets"""

    CREATE_PAYLOAD = {
        "code": "SUN-2026-001",
        "product": "Legacy CRM",
        "sunset_date": "2026-12-31",
        "migration_path": "Migrate to MicroSmart CRM",
        "approved_by": "pmorris",
    }

    async def test_create_sunset(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/development/sunsets", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["product"] == "Legacy CRM"
        assert resp.json()["status"] == "planned"

    async def test_list_sunsets_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/sunsets", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_sunsets_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/development/sunsets", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/development/sunsets", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_sunset_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/sunsets", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/development/sunsets/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_sunset_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/development/sunsets/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_delete_sunset(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/development/sunsets", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/development/sunsets/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200


class TestTechDevelopmentAuth:
    """Auth guard tests for /api/v1/development/*"""

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
        resp = await client.get("/api/v1/development/roadmaps")
        assert resp.status_code == 401

    async def test_viewer_cannot_delete(self, client: AsyncClient):
        """Viewer role must be forbidden from DELETE on roadmaps."""
        viewer_token = await self._register_and_login(client, "viewerdev", "viewer")
        admin_token = await self._register_and_login(client, "adminfordev", "admin")

        create = await client.post(
            "/api/v1/development/roadmaps",
            json={
                "code": "PLN-P4-999",
                "title": "Delete Test",
                "product_line": "SAAS",
                "year": 2026,
                "vision": "Test vision",
                "strategic_goals": "Test goals",
            },
            headers=_auth(admin_token),
        )
        assert create.status_code == 201, create.text
        rm_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/development/roadmaps/{rm_id}",
            headers=_auth(viewer_token),
        )
        assert resp.status_code == 403
        assert "not allowed" in resp.text

    async def test_viewer_can_create(self, client: AsyncClient):
        """Viewer role must be forbidden from POST (create)."""
        token = await self._register_and_login(client, "viewerdev2", "viewer")

        resp = await client.post(
            "/api/v1/development/roadmaps",
            json={
                "code": "PLN-P4-998",
                "title": "Viewer Roadmap",
                "product_line": "SERVICIOS",
                "year": 2026,
                "vision": "Viewer test",
                "strategic_goals": "Viewer goals",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 403, resp.text

    async def test_admin_can_create_roadmap(self, client: AsyncClient):
        token = await self._register_and_login(client, "admindev1", "admin")
        resp = await client.post(
            "/api/v1/development/roadmaps",
            json={
                "code": "PLN-P4-050", "title": "Admin Roadmap", "product_line": "SAAS",
                "year": 2026, "vision": "Admin test", "strategic_goals": "Admin goals",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text

    async def test_manager_can_create_roadmap(self, client: AsyncClient):
        token = await self._register_and_login(client, "mgrdev1", "manager")
        resp = await client.post(
            "/api/v1/development/roadmaps",
            json={
                "code": "PLN-P4-051", "title": "Manager Roadmap", "product_line": "SAAS",
                "year": 2026, "vision": "Manager test", "strategic_goals": "Manager goals",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text

    async def test_admin_can_delete_roadmap(self, client: AsyncClient):
        token = await self._register_and_login(client, "admindev2", "admin")
        create = await client.post(
            "/api/v1/development/roadmaps",
            json={
                "code": "PLN-P4-052", "title": "Delete Test", "product_line": "SAAS",
                "year": 2026, "vision": "Test", "strategic_goals": "Test",
            },
            headers=_auth(token),
        )
        assert create.status_code == 201, create.text
        rm_id = create.json()["id"]
        resp = await client.delete(
            f"/api/v1/development/roadmaps/{rm_id}",
            headers=_auth(token),
        )
        assert resp.status_code == 200
