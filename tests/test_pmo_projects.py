"""Integration tests — PMO Projects (P5) CRUD + business logic (with auth).

NOTE: This module has NO @router.delete endpoints.  Delete tests check that
DELETE returns 405 (Method Not Allowed) rather than 403, because the admin/
manager role check only applies when a DELETE handler exists.
"""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjects:
    """/api/v1/projects/projects"""

    CREATE_PAYLOAD = {
        "code": "PROJ-2026-001",
        "name": "ERP Implementation",
        "product_line": "SERVICIOS",
        "start_date": "2026-03-01",
        "project_manager": "pmartin",
    }

    async def test_create_project(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/projects/projects", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "PROJ-2026-001"
        assert body["status"] == "kicked_off"

    async def test_list_projects_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/projects/projects", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_projects_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/projects/projects", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/projects/projects", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "ERP Implementation"

    async def test_get_project_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/projects/projects", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/projects/projects/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_project_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/projects/projects/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_project(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/projects/projects", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/projects/projects/{created['id']}",
            json={"name": "Updated ERP Implementation"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated ERP Implementation"

    async def test_filter_by_product_line(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/projects/projects", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        await client.post(
            "/api/v1/projects/projects", json={
                **self.CREATE_PAYLOAD,
                "code": "PROJ-2026-002",
                "product_line": "SAAS",
            },
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/projects/projects?product_line=SERVICIOS",
            headers=_auth(admin_token),
        )
        data = resp.json()
        assert all(d["product_line"] == "SERVICIOS" for d in data)


class TestChangeRequests:
    """/api/v1/projects/{project_id}/change-requests — requires a project."""

    async def _create_project(self, client, token):
        resp = await client.post(
            "/api/v1/projects/projects", json={
                "code": "PROJ-CR-001",
                "name": "CR Test Project",
                "product_line": "SERVICIOS",
                "start_date": "2026-04-01",
                "project_manager": "tester",
            },
            headers=_auth(token),
        )
        return resp.json()

    async def test_create_change_request(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        resp = await client.post(
            f"/api/v1/projects/projects/{project['id']}/change-requests", json={
                "code": "CR-2026-001",
                "description": "Add new reporting module",
                "reason": "Client requirement change",
                "requested_by": "pmartin",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["status"] == "submitted"

    async def test_list_change_requests_empty(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        resp = await client.get(
            f"/api/v1/projects/projects/{project['id']}/change-requests",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_change_requests_after_create(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        await client.post(
            f"/api/v1/projects/projects/{project['id']}/change-requests", json={
                "code": "CR-2026-002",
                "description": "Add audit trail",
                "reason": "Compliance requirement",
                "requested_by": "qa_team",
            },
            headers=_auth(admin_token),
        )
        resp = await client.get(
            f"/api/v1/projects/projects/{project['id']}/change-requests",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_change_request_by_id(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        cr = (await client.post(
            f"/api/v1/projects/projects/{project['id']}/change-requests", json={
                "code": "CR-2026-003",
                "description": "Change scope",
                "reason": "Budget adjustment",
                "requested_by": "manager",
            },
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/projects/change-requests/{cr['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == cr["id"]

    async def test_get_change_request_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/projects/change-requests/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestWeeklyReports:
    """/api/v1/projects/{project_id}/weekly-reports — requires a project."""

    async def _create_project(self, client, token):
        resp = await client.post(
            "/api/v1/projects/projects", json={
                "code": "PROJ-WR-001",
                "name": "Weekly Report Project",
                "product_line": "SAAS",
                "start_date": "2026-05-01",
                "project_manager": "scrum_master",
            },
            headers=_auth(token),
        )
        return resp.json()

    async def test_create_weekly_report(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        resp = await client.post(
            f"/api/v1/projects/projects/{project['id']}/weekly-reports", json={
                "week_number": 14,
                "year": 2026,
                "accomplishments": "Completed sprint backlog",
                "next_week_plan": "Start new sprint",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text

    async def test_list_weekly_reports_empty(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        resp = await client.get(
            f"/api/v1/projects/projects/{project['id']}/weekly-reports",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_weekly_reports_after_create(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        await client.post(
            f"/api/v1/projects/projects/{project['id']}/weekly-reports", json={
                "week_number": 15,
                "year": 2026,
                "accomplishments": "Code review completed",
                "next_week_plan": "Deploy to staging",
            },
            headers=_auth(admin_token),
        )
        resp = await client.get(
            f"/api/v1/projects/projects/{project['id']}/weekly-reports",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_weekly_report_by_id(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        wr = (await client.post(
            f"/api/v1/projects/projects/{project['id']}/weekly-reports", json={
                "week_number": 16,
                "year": 2026,
                "accomplishments": "Integration tests pass",
                "next_week_plan": "Performance testing",
            },
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/projects/weekly-reports/{wr['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == wr["id"]

    async def test_get_weekly_report_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/projects/weekly-reports/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestFollowUpMeetings:
    """/api/v1/projects/{project_id}/follow-up-meetings — requires a project."""

    async def _create_project(self, client, token):
        resp = await client.post(
            "/api/v1/projects/projects", json={
                "code": "PROJ-FUM-001",
                "name": "Follow-up Meeting Project",
                "product_line": "SERVICIOS",
                "start_date": "2026-06-01",
                "project_manager": "coordinator",
            },
            headers=_auth(token),
        )
        return resp.json()

    async def test_create_follow_up_meeting(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        resp = await client.post(
            f"/api/v1/projects/projects/{project['id']}/follow-up-meetings", json={
                "date": "2026-06-15",
                "minutes": "Discussed project status and blockers",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text

    async def test_list_follow_up_meetings_empty(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        resp = await client.get(
            f"/api/v1/projects/projects/{project['id']}/follow-up-meetings",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_follow_up_meetings_after_create(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        await client.post(
            f"/api/v1/projects/projects/{project['id']}/follow-up-meetings", json={
                "date": "2026-06-22",
                "minutes": "Second meeting notes",
            },
            headers=_auth(admin_token),
        )
        resp = await client.get(
            f"/api/v1/projects/projects/{project['id']}/follow-up-meetings",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_follow_up_meeting_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/projects/follow-up-meetings/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestHandoverAcceptance:
    """/api/v1/projects/{project_id}/handover-acceptance — requires a project."""

    async def _create_project(self, client, token):
        resp = await client.post(
            "/api/v1/projects/projects", json={
                "code": "PROJ-HA-001",
                "name": "Handover Project",
                "product_line": "SAAS",
                "start_date": "2026-07-01",
                "project_manager": "delivery_lead",
            },
            headers=_auth(token),
        )
        return resp.json()

    async def test_create_handover_acceptance(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        resp = await client.post(
            f"/api/v1/projects/projects/{project['id']}/handover-acceptance", json={
                "accepted_by": "client_rep",
                "comments": "All deliverables accepted",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["status"] == "pending"

    async def test_get_handover_acceptance_not_found(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        resp = await client.get(
            f"/api/v1/projects/projects/{project['id']}/handover-acceptance",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_sign_handover_acceptance(self, client: AsyncClient, admin_token: str):
        project = await self._create_project(client, admin_token)
        ha = (await client.post(
            f"/api/v1/projects/projects/{project['id']}/handover-acceptance", json={
                "accepted_by": "client",
            },
            headers=_auth(admin_token),
        )).json()
        resp = await client.post(
            f"/api/v1/projects/handover-acceptance/{ha['id']}/sign",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "signed"


class TestPmoProjectsAuth:
    """Auth tests for PMO projects endpoints."""

    async def test_unauthenticated_list_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/projects/projects")
        assert resp.status_code == 401

    async def test_viewer_can_create(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "pmo_viewer", "email": "pmo_viewer@test.com",
            "password": "password123", "role": "viewer",
        })
        login = await client.post("/auth/login", json={
            "username": "pmo_viewer", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.post(
            "/api/v1/projects/projects",
            json=TestProjects.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_delete(self, client: AsyncClient):
        """No DELETE endpoints exist in PMO projects; verify 405."""
        await client.post("/auth/register", json={
            "username": "pmo_viewer_del", "email": "pmo_viewer_del@test.com",
            "password": "password123", "role": "viewer",
        })
        login = await client.post("/auth/login", json={
            "username": "pmo_viewer_del", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.delete(
            "/api/v1/projects/projects/1",
            headers=_auth(token),
        )
        assert resp.status_code == 405

    async def test_admin_can_create_project(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "pmo_admin", "email": "pmo_admin@test.com",
            "password": "password123", "role": "admin",
        })
        login = await client.post("/auth/login", json={
            "username": "pmo_admin", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.post(
            "/api/v1/projects/projects",
            json=TestProjects.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text

    async def test_manager_can_create_project(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "pmo_mgr", "email": "pmo_mgr@test.com",
            "password": "password123", "role": "manager",
        })
        login = await client.post("/auth/login", json={
            "username": "pmo_mgr", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.post(
            "/api/v1/projects/projects",
            json=TestProjects.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text
