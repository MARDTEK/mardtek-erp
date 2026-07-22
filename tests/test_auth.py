"""Integration tests for auth module — login, register, me, and role protection."""

from httpx import AsyncClient


class TestAuthRegister:
    """/auth/register"""

    async def test_register(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "role": "viewer",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["role"] == "viewer"
        assert "password" not in data

    async def test_register_duplicate_username(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "dupuser",
            "email": "dup@example.com",
            "password": "password123",
            "role": "viewer",
        })
        resp = await client.post("/auth/register", json={
            "username": "dupuser",
            "email": "other@example.com",
            "password": "password123",
            "role": "viewer",
        })
        assert resp.status_code == 409

    async def test_register_invalid_role(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={
            "username": "badrole",
            "email": "bad@example.com",
            "password": "password123",
            "role": "superadmin",
        })
        assert resp.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={
            "username": "shortpass",
            "email": "short@example.com",
            "password": "123",
            "role": "viewer",
        })
        assert resp.status_code == 422


class TestAuthLogin:
    """/auth/login"""

    async def _register_user(self, client: AsyncClient, username: str = "loginuser"):
        await client.post("/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "password123",
            "role": "editor",
        })

    async def test_login_success(self, client: AsyncClient):
        await self._register_user(client)
        resp = await client.post("/auth/login", json={
            "username": "loginuser",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "loginuser"
        assert data["user"]["role"] == "editor"

    async def test_login_wrong_password(self, client: AsyncClient):
        await self._register_user(client, "wrongpass")
        resp = await client.post("/auth/login", json={
            "username": "wrongpass",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/auth/login", json={
            "username": "nobody",
            "password": "password123",
        })
        assert resp.status_code == 401


class TestAuthMe:
    """/auth/me"""

    async def _register_and_login(self, client: AsyncClient, username: str = "metest") -> str:
        await client.post("/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "password123",
            "role": "manager",
        })
        resp = await client.post("/auth/login", json={
            "username": username,
            "password": "password123",
        })
        return resp.json()["access_token"]

    async def test_me_with_token(self, client: AsyncClient):
        token = await self._register_and_login(client)
        resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "metest"
        assert data["role"] == "manager"

    async def test_me_without_token(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        # HTTPBearer returns 401 when the header is completely missing
        assert resp.status_code == 401

    async def test_me_with_invalid_token(self, client: AsyncClient):
        resp = await client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401


class TestRoleProtection:
    """Verify RoleChecker blocks unauthorized roles on protected endpoints."""

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

    async def test_viewer_cannot_delete_document(self, client: AsyncClient):
        """A viewer token must NOT be allowed to call a DELETE endpoint."""
        token = await self._register_and_login(client, "vieweruser", "viewer")

        # Create a document first (any authenticated user can POST)
        create = await client.post(
            "/api/v1/quality/documents",
            json={
                "code": "SOP-P2-001-QM",
                "title": "Delete Test",
                "process_code": "P2",
                "doc_type": "SOP",
                "next_review_at": "2027-01-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create.status_code == 201, create.text
        doc_id = create.json()["id"]

        # Viewer must be forbidden from deleting
        resp = await client.delete(
            f"/api/v1/quality/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert "not allowed" in resp.text

    async def test_editor_cannot_delete_document(self, client: AsyncClient):
        """An editor token must NOT be allowed to call a DELETE endpoint."""
        token = await self._register_and_login(client, "editoruser", "editor")

        create = await client.post(
            "/api/v1/quality/documents",
            json={
                "code": "SOP-P2-002-QM",
                "title": "Delete Test 2",
                "process_code": "P2",
                "doc_type": "SOP",
                "next_review_at": "2027-01-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create.status_code == 201, create.text
        doc_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/quality/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_admin_can_delete_document(self, client: AsyncClient):
        """Admin must be allowed to delete."""
        token = await self._register_and_login(client, "adminuser", "admin")

        create = await client.post(
            "/api/v1/quality/documents",
            json={
                "code": "SOP-P2-003-QM",
                "title": "Delete Test 3",
                "process_code": "P2",
                "doc_type": "SOP",
                "next_review_at": "2027-01-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create.status_code == 201, create.text
        doc_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/quality/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_unauthenticated_request_blocked(self, client: AsyncClient):
        """No token → 401 for any protected endpoint."""
        resp = await client.get("/api/v1/quality/documents")
        assert resp.status_code == 401
