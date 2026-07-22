"""Integration tests — Commercial Sales CRM CRUD + auth."""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestLeads:
    """/api/v1/commercial/leads"""

    CREATE_PAYLOAD = {
        "company": "Acme Corp",
        "contact_name": "John Smith",
        "contact_email": "john@acme.com",
        "source": "website",
        "product_line": "SERVICIOS",
    }

    async def test_create_lead(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/commercial/leads", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["company"] == "Acme Corp"
        assert body["status"] == "new"

    async def test_list_leads_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/commercial/leads", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_leads_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/commercial/leads", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/commercial/leads", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["company"] == "Acme Corp"

    async def test_get_lead_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/commercial/leads", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/commercial/leads/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_lead_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/commercial/leads/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_lead(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/commercial/leads", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/commercial/leads/{created['id']}",
            json={"company": "Updated Corp"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["company"] == "Updated Corp"


class TestDiscovery:
    """/api/v1/commercial/leads/{lead_id}/discovery"""

    async def _create_lead(self, client: AsyncClient, token: str) -> dict:
        resp = await client.post(
            "/api/v1/commercial/leads",
            json={"company": "Discovery Inc", "contact_name": "D Bob", "contact_email": "db@test.com", "source": "referral", "product_line": "SAAS"},
            headers=_auth(token),
        )
        return resp.json()

    async def test_create_discovery(self, client: AsyncClient, admin_token: str):
        lead = await self._create_lead(client, admin_token)
        resp = await client.post(
            f"/api/v1/commercial/leads/{lead['id']}/discovery",
            json={"needs": "CRM integration", "recorded_by": "salesrep1"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["needs"] == "CRM integration"

    async def test_get_discovery(self, client: AsyncClient, admin_token: str):
        lead = await self._create_lead(client, admin_token)
        await client.post(
            f"/api/v1/commercial/leads/{lead['id']}/discovery",
            json={"needs": "API training", "recorded_by": "salesrep2"},
            headers=_auth(admin_token),
        )
        resp = await client.get(
            f"/api/v1/commercial/leads/{lead['id']}/discovery",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["needs"] == "API training"

    async def test_get_discovery_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/commercial/leads/99999/discovery",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_create_discovery_duplicate(self, client: AsyncClient, admin_token: str):
        lead = await self._create_lead(client, admin_token)
        payload = {"needs": "First discovery", "recorded_by": "rep"}
        await client.post(
            f"/api/v1/commercial/leads/{lead['id']}/discovery",
            json=payload, headers=_auth(admin_token),
        )
        resp = await client.post(
            f"/api/v1/commercial/leads/{lead['id']}/discovery",
            json=payload, headers=_auth(admin_token),
        )
        assert resp.status_code == 409


class TestProposals:
    """/api/v1/commercial/leads/{lead_id}/proposals — success path has a
    known router bug (reused <https://github.com/anomalyco/opencode/issues/1>)."""

    async def test_proposal_not_found_lead(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/commercial/leads/99999/proposals",
            json={"total_amount": 5000.00, "created_by": "nobody"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestIcpMatrix:
    """/api/v1/commercial/icp-matrix"""

    CREATE_PAYLOAD = {
        "industry": "Technology",
        "company_size": "50-200",
        "role": "CTO",
        "pain_points": "Scaling infrastructure",
    }

    async def test_create_icp_entry(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/commercial/icp-matrix", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["industry"] == "Technology"

    async def test_list_icp_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/commercial/icp-matrix", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_icp_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/commercial/icp-matrix", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/commercial/icp-matrix", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["industry"] == "Technology"


class TestCommercialAuth:
    """Auth protection for Commercial Sales endpoints."""

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
        resp = await client.get("/api/v1/commercial/leads")
        assert resp.status_code == 401

    async def test_viewer_cannot_delete_lead(self, client: AsyncClient):
        token = await self._register_and_login(client, "comviewer", "viewer")

        create = await client.post(
            "/api/v1/commercial/leads",
            json={"company": "Auth Corp", "contact_name": "Auth U", "contact_email": "au@test.com", "source": "web", "product_line": "SERVICIOS"},
            headers=_auth(token),
        )
        assert create.status_code == 201, create.text
        lead_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/commercial/leads/{lead_id}",
            headers=_auth(token),
        )
        assert resp.status_code == 405

    async def test_viewer_can_create_lead(self, client: AsyncClient):
        token = await self._register_and_login(client, "comviewer2", "viewer")
        resp = await client.post(
            "/api/v1/commercial/leads",
            json={"company": "Viewer Ltd", "contact_name": "V User", "contact_email": "vu@test.com", "source": "cold-call", "product_line": "SAAS"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
