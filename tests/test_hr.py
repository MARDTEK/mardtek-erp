"""Integration tests — Human Resources (P7) CRUD + auth."""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestJobDescriptions:
    """/api/v1/hr/job-descriptions"""

    CREATE_PAYLOAD = {
        "code": "JD-001",
        "title": "Software Engineer",
        "department": "Engineering",
        "responsibilities": "Develop and maintain software",
        "requirements": "5+ years experience",
    }

    async def test_create_job_description(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/hr/job-descriptions", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "JD-001"
        assert body["title"] == "Software Engineer"
        assert body["is_active"] is True

    async def test_list_job_descriptions_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/job-descriptions", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_job_descriptions_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/hr/job-descriptions", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/hr/job-descriptions", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Software Engineer"

    async def test_get_job_description_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/job-descriptions", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/hr/job-descriptions/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_job_description_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/job-descriptions/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_job_description(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/job-descriptions", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/hr/job-descriptions/{created['id']}",
            json={"title": "Senior Software Engineer"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Senior Software Engineer"

    async def test_delete_job_description(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/job-descriptions", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/hr/job-descriptions/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 204

        get_resp = await client.get(
            f"/api/v1/hr/job-descriptions/{created['id']}",
            headers=_auth(admin_token),
        )
        assert get_resp.status_code == 404


class TestPersonnelRequests:
    """/api/v1/hr/personnel-requests"""

    CREATE_PAYLOAD = {
        "code": "PR-001",
        "requested_by": "manager1",
        "job_title": "Data Analyst",
        "department": "Analytics",
        "justification": "New team role",
        "budget": 60000.00,
    }

    async def test_create_personnel_request(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/hr/personnel-requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "PR-001"
        assert body["status"] == "open"

    async def test_list_personnel_requests_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/personnel-requests", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_personnel_requests_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/hr/personnel-requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/hr/personnel-requests", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["job_title"] == "Data Analyst"

    async def test_get_personnel_request_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/personnel-requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/hr/personnel-requests/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_personnel_request_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/personnel-requests/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_personnel_request(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/personnel-requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/hr/personnel-requests/{created['id']}",
            json={"justification": "Updated justification"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["justification"] == "Updated justification"


class TestStaffRegister:
    """/api/v1/hr/staff"""

    CREATE_PAYLOAD = {
        "employee_name": "John Doe",
        "email": "jdoe@company.com",
        "department": "Engineering",
        "position": "Developer",
        "hire_date": "2026-01-15",
        "contract_type": "permanent",
    }

    async def test_create_staff(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/hr/staff", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["employee_name"] == "John Doe"
        assert body["status"] == "active"

    async def test_list_staff_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/staff", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_staff_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/hr/staff", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/hr/staff", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["employee_name"] == "John Doe"

    async def test_get_staff_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/staff", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/hr/staff/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_staff_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/staff/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_staff(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/staff", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/hr/staff/{created['id']}",
            json={"position": "Senior Developer"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["position"] == "Senior Developer"

    async def test_delete_staff(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/staff", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/hr/staff/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 204

        get_resp = await client.get(
            f"/api/v1/hr/staff/{created['id']}",
            headers=_auth(admin_token),
        )
        assert get_resp.status_code == 404


class TestPerformanceEvaluations:
    """/api/v1/hr/evaluations"""

    CREATE_PAYLOAD = {
        "employee_name": "Jane Smith",
        "evaluator": "Manager A",
        "period": "2026-Q1",
    }

    async def test_create_evaluation(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/hr/evaluations", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["employee_name"] == "Jane Smith"
        assert body["status"] == "draft"

    async def test_list_evaluations_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/evaluations", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_evaluations_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/hr/evaluations", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/hr/evaluations", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["period"] == "2026-Q1"

    async def test_get_evaluation_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/evaluations", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/hr/evaluations/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_evaluation_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/evaluations/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_evaluation(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/evaluations", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/hr/evaluations/{created['id']}",
            json={"score": 4},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["score"] == 4


class TestLaborIncidents:
    """/api/v1/hr/labor-incidents"""

    CREATE_PAYLOAD = {
        "code": "LI-001",
        "employee_name": "John Doe",
        "incident_type": "warning",
        "description": "Late arrival on multiple occasions",
    }

    async def test_create_labor_incident(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/hr/labor-incidents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "LI-001"
        assert body["status"] == "open"

    async def test_list_labor_incidents_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/labor-incidents", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_labor_incidents_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/hr/labor-incidents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/hr/labor-incidents", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["incident_type"] == "warning"

    async def test_get_labor_incident_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/labor-incidents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/hr/labor-incidents/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_labor_incident_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/labor-incidents/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_labor_incident(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/labor-incidents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/hr/labor-incidents/{created['id']}",
            json={"description": "Updated description"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated description"


class TestInductionChecklists:
    """/api/v1/hr/induction-checklists"""

    CREATE_PAYLOAD = {
        "employee_name": "New Employee",
        "hire_date": "2026-03-01",
    }

    async def test_create_induction_checklist(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/hr/induction-checklists", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["employee_name"] == "New Employee"
        assert body["status"] == "in_progress"

    async def test_list_induction_checklists_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/induction-checklists", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_induction_checklists_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/hr/induction-checklists", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/hr/induction-checklists", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["employee_name"] == "New Employee"

    async def test_get_induction_checklist_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/induction-checklists", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/hr/induction-checklists/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_induction_checklist_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/induction-checklists/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_induction_checklist(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/induction-checklists", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/hr/induction-checklists/{created['id']}",
            json={"status": "completed"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


class TestIndividualDevelopmentPlans:
    """/api/v1/hr/development-plans"""

    CREATE_PAYLOAD = {
        "employee_name": "Alice Johnson",
    }

    async def test_create_development_plan(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/hr/development-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["employee_name"] == "Alice Johnson"
        assert body["status"] == "active"

    async def test_list_development_plans_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/development-plans", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_development_plans_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/hr/development-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/hr/development-plans", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["employee_name"] == "Alice Johnson"

    async def test_get_development_plan_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/development-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/hr/development-plans/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_development_plan_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/hr/development-plans/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_development_plan(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/hr/development-plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/hr/development-plans/{created['id']}",
            json={"status": "completed"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


class TestHrAuth:
    """Auth protection for HR endpoints."""

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
        resp = await client.get("/api/v1/hr/job-descriptions")
        assert resp.status_code == 401

    async def test_viewer_cannot_delete_job_description(self, client: AsyncClient):
        token = await self._register_and_login(client, "hrviewer", "viewer")

        create = await client.post(
            "/api/v1/hr/job-descriptions",
            json={"code": "JD-AUTH01", "title": "Auth Test", "department": "Eng", "responsibilities": "Testing", "requirements": "None"},
            headers=_auth(token),
        )
        assert create.status_code == 201, create.text
        jd_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/hr/job-descriptions/{jd_id}",
            headers=_auth(token),
        )
        assert resp.status_code == 403

    async def test_viewer_can_create_job_description(self, client: AsyncClient):
        token = await self._register_and_login(client, "hrviewer2", "viewer")
        resp = await client.post(
            "/api/v1/hr/job-descriptions",
            json={"code": "JD-AUTH02", "title": "Viewer Created", "department": "Eng", "responsibilities": "Test", "requirements": "Test"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
