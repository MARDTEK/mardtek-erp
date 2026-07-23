"""Integration tests — P3 OKF compliance: quote accept + contract create."""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


LEAD_PAYLOAD = {
    "company": "Test Corp",
    "contact_name": "Jane Doe",
    "contact_email": "jane@test.com",
    "source": "referral",
    "product_line": "SAAS",
}


async def _create_lead(client: AsyncClient, token: str) -> dict:
    resp = await client.post(
        "/api/v1/commercial/leads", json=LEAD_PAYLOAD, headers=_auth(token),
    )
    return resp.json()


async def _create_quote(client: AsyncClient, token: str, lead_id: int) -> dict:
    resp = await client.post(
        f"/api/v1/commercial/leads/{lead_id}/quotes",
        json={
            "subtotal": "1000.00",
            "total": "1000.00",
            "created_by": "tester",
        },
        headers=_auth(token),
    )
    return resp.json()


async def _send_quote(client: AsyncClient, token: str, quote_id: int) -> dict:
    resp = await client.post(
        f"/api/v1/commercial/quotes/{quote_id}/send",
        headers=_auth(token),
    )
    return resp.json()


class TestAcceptQuote:
    """POST /quotes/{quote_id}/accept"""

    async def test_accept_sent_quote(self, client: AsyncClient, admin_token: str):
        lead = await _create_lead(client, admin_token)
        quote = await _create_quote(client, admin_token, lead["id"])
        await _send_quote(client, admin_token, quote["id"])

        resp = await client.post(
            f"/api/v1/commercial/quotes/{quote['id']}/accept",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "accepted"
        assert body["accepted_at"] is not None

    async def test_accept_quote_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/commercial/quotes/99999/accept",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_accept_draft_quote_fails(self, client: AsyncClient, admin_token: str):
        lead = await _create_lead(client, admin_token)
        quote = await _create_quote(client, admin_token, lead["id"])

        resp = await client.post(
            f"/api/v1/commercial/quotes/{quote['id']}/accept",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 400
        assert "Only sent quotes" in resp.json()["detail"]


class TestCreateContract:
    """POST /contracts"""

    async def test_create_sow_contract(self, client: AsyncClient, admin_token: str):
        lead = await _create_lead(client, admin_token)
        resp = await client.post(
            "/api/v1/commercial/contracts",
            json={
                "lead_id": lead["id"],
                "contract_type": "sow",
                "start_date": "2026-08-01",
                "total_value": "50000.00",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["contract_type"] == "sow"
        assert body["contract_number"].startswith("CTR-")
        assert body["signed_at"] is not None
        assert body["total_value"] == "50000.00"

    async def test_create_subscription_contract(self, client: AsyncClient, admin_token: str):
        lead = await _create_lead(client, admin_token)
        resp = await client.post(
            "/api/v1/commercial/contracts",
            json={
                "lead_id": lead["id"],
                "contract_type": "subscription",
                "start_date": "2026-08-01",
                "total_value": "1200.00",
                "monthly_value": "100.00",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["contract_type"] == "subscription"
        assert body["monthly_value"] == "100.00"

    async def test_create_contract_lead_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/commercial/contracts",
            json={
                "lead_id": 99999,
                "contract_type": "sow",
                "start_date": "2026-08-01",
                "total_value": "50000.00",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_create_contract_invalid_type(self, client: AsyncClient, admin_token: str):
        lead = await _create_lead(client, admin_token)
        resp = await client.post(
            "/api/v1/commercial/contracts",
            json={
                "lead_id": lead["id"],
                "contract_type": "invalid",
                "start_date": "2026-08-01",
                "total_value": "50000.00",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
