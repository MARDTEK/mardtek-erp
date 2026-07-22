"""Integration tests — Customer Experience (P10) CRUD (with auth)."""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestNpsSurveys:
    """/api/v1/customer-satisfaction/nps-surveys"""

    CREATE_PAYLOAD = {
        "code": "NPS-2026-001",
        "customer_email": "client@example.com",
        "score": 9,
    }

    async def test_create_nps_survey(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/customer-satisfaction/nps-surveys", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "NPS-2026-001"
        assert body["category"] == "promoter"

    async def test_list_nps_surveys_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/nps-surveys", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_nps_surveys_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/customer-satisfaction/nps-surveys", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/customer-satisfaction/nps-surveys", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["customer_email"] == "client@example.com"

    async def test_get_nps_survey_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/customer-satisfaction/nps-surveys", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/customer-satisfaction/nps-surveys/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_nps_survey_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/nps-surveys/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestCsatSurveys:
    """/api/v1/customer-satisfaction/csat-surveys"""

    CREATE_PAYLOAD = {
        "code": "CSAT-2026-001",
        "customer_email": "service@example.com",
        "score": 4,
    }

    async def test_create_csat_survey(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/customer-satisfaction/csat-surveys", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["code"] == "CSAT-2026-001"

    async def test_list_csat_surveys_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/csat-surveys", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_csat_surveys_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/customer-satisfaction/csat-surveys", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/customer-satisfaction/csat-surveys", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_csat_survey_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/customer-satisfaction/csat-surveys", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/customer-satisfaction/csat-surveys/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_csat_survey_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/csat-surveys/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestCesSurveys:
    """/api/v1/customer-satisfaction/ces-surveys"""

    CREATE_PAYLOAD = {
        "code": "CES-2026-001",
        "customer_email": "support@example.com",
        "score": 3,
        "task_description": "Resolve login issue",
    }

    async def test_create_ces_survey(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/customer-satisfaction/ces-surveys", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["task_description"] == "Resolve login issue"

    async def test_list_ces_surveys_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/ces-surveys", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_ces_surveys_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/customer-satisfaction/ces-surveys", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/customer-satisfaction/ces-surveys", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_ces_survey_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/customer-satisfaction/ces-surveys", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/customer-satisfaction/ces-surveys/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_ces_survey_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/ces-surveys/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestComplaintClaims:
    """/api/v1/customer-satisfaction/complaints"""

    CREATE_PAYLOAD = {
        "code": "CMP-2026-001",
        "customer_email": "client@example.com",
        "type": "complaint",
        "description": "Delayed response time",
    }

    async def test_create_complaint(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/customer-satisfaction/complaints", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["code"] == "CMP-2026-001"
        assert resp.json()["status"] == "open"

    async def test_list_complaints_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/complaints", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_complaints_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/customer-satisfaction/complaints", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/customer-satisfaction/complaints", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_complaint_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/customer-satisfaction/complaints", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/customer-satisfaction/complaints/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_complaint_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/complaints/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestComplaintRegister:
    """/api/v1/customer-satisfaction/complaint-register"""

    async def test_create_complaint_register(self, client: AsyncClient, admin_token: str):
        complaint = (await client.post(
            "/api/v1/customer-satisfaction/complaints",
            json={
                "code": "CMP-2026-010",
                "customer_email": "reg@example.com",
                "type": "claim",
                "description": "Billing issue",
            },
            headers=_auth(admin_token),
        )).json()

        resp = await client.post(
            "/api/v1/customer-satisfaction/complaint-register",
            json={"complaint_id": complaint["id"], "category": "billing"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["category"] == "billing"

    async def test_list_complaint_register_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/complaint-register", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_complaint_register_after_create(self, client: AsyncClient, admin_token: str):
        complaint = (await client.post(
            "/api/v1/customer-satisfaction/complaints",
            json={
                "code": "CMP-2026-011",
                "customer_email": "reg2@example.com",
                "type": "complaint",
                "description": "Quality issue",
            },
            headers=_auth(admin_token),
        )).json()
        await client.post(
            "/api/v1/customer-satisfaction/complaint-register",
            json={"complaint_id": complaint["id"], "category": "quality"},
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/customer-satisfaction/complaint-register", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_complaint_register_by_id(self, client: AsyncClient, admin_token: str):
        complaint = (await client.post(
            "/api/v1/customer-satisfaction/complaints",
            json={
                "code": "CMP-2026-012",
                "customer_email": "reg3@example.com",
                "type": "claim",
                "description": "Refund request",
            },
            headers=_auth(admin_token),
        )).json()
        created = (await client.post(
            "/api/v1/customer-satisfaction/complaint-register",
            json={"complaint_id": complaint["id"], "category": "refund"},
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/customer-satisfaction/complaint-register/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_complaint_register_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/complaint-register/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_create_complaint_register_nonexistent_complaint(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/customer-satisfaction/complaint-register",
            json={"complaint_id": 99999, "category": "billing"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestExitInterviews:
    """/api/v1/customer-satisfaction/exit-interviews"""

    CREATE_PAYLOAD = {
        "code": "EXIT-2026-001",
        "subscription_id": 1,
        "churn_reason_category": "price",
    }

    async def test_create_exit_interview(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/customer-satisfaction/exit-interviews", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["churn_reason_category"] == "price"

    async def test_list_exit_interviews_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/exit-interviews", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_exit_interviews_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/customer-satisfaction/exit-interviews", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/customer-satisfaction/exit-interviews", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_exit_interview_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/customer-satisfaction/exit-interviews", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/customer-satisfaction/exit-interviews/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_exit_interview_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/exit-interviews/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestSatisfactionReports:
    """/api/v1/customer-satisfaction/reports"""

    CREATE_PAYLOAD = {
        "code": "SAT-RPT-2026-001",
        "period": "2026-Q1",
    }

    async def test_create_report(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/customer-satisfaction/reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["period"] == "2026-Q1"

    async def test_list_reports_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/reports", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_reports_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/customer-satisfaction/reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/customer-satisfaction/reports", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_report_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/customer-satisfaction/reports", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/customer-satisfaction/reports/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_report_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/customer-satisfaction/reports/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestCustomerExperienceAuth:
    """Auth guard tests for /api/v1/customer-satisfaction/*"""

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
        resp = await client.get("/api/v1/customer-satisfaction/nps-surveys")
        assert resp.status_code == 401

    async def test_viewer_can_create(self, client: AsyncClient):
        """Viewer role must be allowed to POST (create)."""
        token = await self._register_and_login(client, "viewercx", "viewer")

        resp = await client.post(
            "/api/v1/customer-satisfaction/nps-surveys",
            json={
                "code": "NPS-2026-999",
                "customer_email": "viewer@test.com",
                "score": 7,
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["customer_email"] == "viewer@test.com"
