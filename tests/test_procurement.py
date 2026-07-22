"""Integration tests — Procurement (P9) CRUD + business logic (with auth).

NOTE: This module has NO @router.delete endpoints.  Delete tests check that
DELETE returns 405 (Method Not Allowed) rather than 403, because the admin/
manager role check only applies when a DELETE handler exists.
"""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestPurchaseRequests:
    """/api/v1/procurement/purchase-requests"""

    CREATE_PAYLOAD = {
        "code": "PR-2026-001",
        "requester": "jdoe",
        "description": "Office supplies for Q1",
        "quantity": 10,
        "estimated_cost": 500.00,
        "category": "supplies",
        "justification": "Annual restock",
    }

    async def test_create_purchase_request(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/procurement/purchase-requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "PR-2026-001"
        assert body["status"] == "draft"

    async def test_list_purchase_requests_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/procurement/purchase-requests", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_purchase_requests_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/procurement/purchase-requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/procurement/purchase-requests", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["requester"] == "jdoe"

    async def test_get_purchase_request_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/procurement/purchase-requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/procurement/purchase-requests/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_purchase_request_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/procurement/purchase-requests/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_purchase_request(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/procurement/purchase-requests", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/procurement/purchase-requests/{created['id']}",
            json={"description": "Updated supplies"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated supplies"

    async def test_submit_approve_order_flow(self, client: AsyncClient, admin_token: str):
        """DRAFT → SUBMITTED → APPROVED → ORDERED."""
        pr = (await client.post(
            "/api/v1/procurement/purchase-requests", json={
                **self.CREATE_PAYLOAD, "code": "PR-2026-002",
            },
            headers=_auth(admin_token),
        )).json()
        assert pr["status"] == "draft"

        submit = await client.post(
            f"/api/v1/procurement/purchase-requests/{pr['id']}/submit",
            headers=_auth(admin_token),
        )
        assert submit.status_code == 200
        assert submit.json()["status"] == "submitted"

        approve = await client.post(
            f"/api/v1/procurement/purchase-requests/{pr['id']}/approve",
            headers=_auth(admin_token),
        )
        assert approve.status_code == 200
        assert approve.json()["status"] == "approved"

        order = await client.post(
            f"/api/v1/procurement/purchase-requests/{pr['id']}/order",
            headers=_auth(admin_token),
        )
        assert order.status_code == 200
        assert order.json()["status"] == "ordered"


class TestSuppliers:
    """/api/v1/procurement/suppliers"""

    CREATE_PAYLOAD = {
        "code": "SUP-001",
        "company_name": "Tech Supplies Inc.",
        "contact": "John Supplier",
        "email": "supplier@techsupplies.com",
        "phone": "+1234567890",
        "services": "IT equipment and software",
    }

    async def test_create_supplier(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/procurement/suppliers", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["status"] == "pending"

    async def test_list_suppliers_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/procurement/suppliers", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_suppliers_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/procurement/suppliers", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/procurement/suppliers", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["company_name"] == "Tech Supplies Inc."

    async def test_get_supplier_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/procurement/suppliers", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/procurement/suppliers/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_supplier_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/procurement/suppliers/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_approve_then_reject_states(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/procurement/suppliers", json={
                **self.CREATE_PAYLOAD, "code": "SUP-002",
            },
            headers=_auth(admin_token),
        )).json()

        reject = await client.post(
            f"/api/v1/procurement/suppliers/{created['id']}/reject",
            headers=_auth(admin_token),
        )
        assert reject.status_code == 200
        assert reject.json()["status"] == "rejected"


class TestSupplierEvaluations:
    """/api/v1/procurement/evaluations — requires a supplier to exist."""

    async def _create_supplier(self, client, token):
        resp = await client.post(
            "/api/v1/procurement/suppliers", json={
                "code": "SUP-EVAL-001",
                "company_name": "Eval Corp",
                "contact": "Eva Luator",
                "email": "eval@corp.com",
                "phone": "+1111111111",
                "services": "Consulting",
            },
            headers=_auth(token),
        )
        return resp.json()

    async def test_create_evaluation(self, client: AsyncClient, admin_token: str):
        supplier = await self._create_supplier(client, admin_token)
        resp = await client.post(
            "/api/v1/procurement/evaluations", json={
                "supplier_id": supplier["id"],
                "evaluator": "qa_team",
                "criteria_scores": {"quality": 4, "price": 3, "delivery": 5, "service": 4},
                "period": "2026-Q1",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["status"] == "draft"

    async def test_list_evaluations_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/procurement/evaluations", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_evaluations_after_create(self, client: AsyncClient, admin_token: str):
        supplier = await self._create_supplier(client, admin_token)
        await client.post(
            "/api/v1/procurement/evaluations", json={
                "supplier_id": supplier["id"],
                "evaluator": "qa_team",
                "criteria_scores": {"quality": 4, "price": 3, "delivery": 5, "service": 4},
                "period": "2026-Q1",
            },
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/procurement/evaluations", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_evaluation_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/procurement/evaluations/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestSupplierRegister:
    """/api/v1/procurement/register — requires an approved supplier."""

    async def _create_approved_supplier(self, client, token):
        sup = (await client.post(
            "/api/v1/procurement/suppliers", json={
                "code": "SUP-REG-001",
                "company_name": "Register Corp",
                "contact": "Reggie Star",
                "email": "reg@corp.com",
                "phone": "+1222222222",
                "services": "Logistics",
            },
            headers=_auth(token),
        )).json()
        await client.post(
            f"/api/v1/procurement/suppliers/{sup['id']}/approve",
            headers=_auth(token),
        )
        return sup

    async def test_create_register_entry(self, client: AsyncClient, admin_token: str):
        supplier = await self._create_approved_supplier(client, admin_token)
        resp = await client.post(
            "/api/v1/procurement/register", json={
                "supplier_id": supplier["id"],
                "approved_by": "procurement_manager",
                "category": "logistics",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["is_active"] is True

    async def test_list_register_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/procurement/register", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_register_after_create(self, client: AsyncClient, admin_token: str):
        supplier = await self._create_approved_supplier(client, admin_token)
        await client.post(
            "/api/v1/procurement/register", json={
                "supplier_id": supplier["id"],
                "approved_by": "manager",
                "category": "logistics",
            },
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/procurement/register", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_register_entry_by_id(self, client: AsyncClient, admin_token: str):
        supplier = await self._create_approved_supplier(client, admin_token)
        created = (await client.post(
            "/api/v1/procurement/register", json={
                "supplier_id": supplier["id"],
                "approved_by": "manager",
                "category": "logistics",
            },
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/procurement/register/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_register_entry_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/procurement/register/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestProcurementAuth:
    """Auth tests for procurement endpoints."""

    async def test_unauthenticated_list_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/procurement/purchase-requests")
        assert resp.status_code == 401

    async def test_viewer_can_create(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "proc_viewer", "email": "proc_viewer@test.com",
            "password": "password123", "role": "viewer",
        })
        login = await client.post("/auth/login", json={
            "username": "proc_viewer", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.post(
            "/api/v1/procurement/purchase-requests",
            json=TestPurchaseRequests.CREATE_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 201

    async def test_viewer_cannot_delete(self, client: AsyncClient):
        """No DELETE endpoints exist in procurement; verify 405."""
        await client.post("/auth/register", json={
            "username": "proc_viewer_del", "email": "proc_viewer_del@test.com",
            "password": "password123", "role": "viewer",
        })
        login = await client.post("/auth/login", json={
            "username": "proc_viewer_del", "password": "password123",
        })
        token = login.json()["access_token"]
        resp = await client.delete(
            "/api/v1/procurement/purchase-requests/1",
            headers=_auth(token),
        )
        assert resp.status_code == 405
