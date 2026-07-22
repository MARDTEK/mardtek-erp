"""Integration tests — Training Services (P6) CRUD + auth."""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestTrainingNeeds:
    """/api/v1/training/needs"""

    CREATE_PAYLOAD = {
        "code": "TN-001",
        "employee_name": "Carlos Lopez",
        "role": "Developer",
        "skills_gap": "Kubernetes",
    }

    async def test_create_need(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/training/needs", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "TN-001"
        assert body["priority"] == "medium"

    async def test_list_needs_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/needs", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_needs_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/training/needs", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/training/needs", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["employee_name"] == "Carlos Lopez"

    async def test_get_need_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/needs", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/training/needs/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_need_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/needs/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_need(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/needs", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/training/needs/{created['id']}",
            json={"priority": "high"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["priority"] == "high"


class TestCompetencyMatrices:
    """/api/v1/training/competency-matrices"""

    CREATE_PAYLOAD = {
        "code": "CM-001",
        "role": "Backend Developer",
    }

    async def test_create_competency_matrix(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/training/competency-matrices", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "CM-001"
        assert body["version"] == "1.0"

    async def test_list_competency_matrices_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/competency-matrices", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_competency_matrices_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/training/competency-matrices", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/training/competency-matrices", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["role"] == "Backend Developer"

    async def test_get_competency_matrix_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/competency-matrices", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/training/competency-matrices/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_competency_matrix_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/competency-matrices/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_competency_matrix(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/competency-matrices", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/training/competency-matrices/{created['id']}",
            json={"version": "2.0"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == "2.0"


class TestCourses:
    """/api/v1/training/courses"""

    CREATE_PAYLOAD = {
        "code": "CRS-001",
        "title": "Docker Fundamentals",
        "modality": "online",
        "duration_hours": 16,
        "content": "Container basics, images, compose",
    }

    async def test_create_course(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/training/courses", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "CRS-001"
        assert body["status"] == "draft"

    async def test_list_courses_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/courses", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_courses_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/training/courses", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/training/courses", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Docker Fundamentals"

    async def test_get_course_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/courses", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/training/courses/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_course_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/courses/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_course(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/courses", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/training/courses/{created['id']}",
            json={"title": "Docker Advanced"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Docker Advanced"


class TestTrainingPlans:
    """/api/v1/training/plans"""

    CREATE_PAYLOAD = {
        "code": "PLN-2026",
        "year": 2026,
    }

    async def test_create_plan(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/training/plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "PLN-2026"
        assert body["status"] == "draft"

    async def test_list_plans_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/plans", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_plans_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/training/plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/training/plans", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["year"] == 2026

    async def test_get_plan_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/training/plans/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_plan_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/plans/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_plan(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/plans", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/training/plans/{created['id']}",
            json={"budget": 50000.0},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["budget"] == 50000.0


class TestTrainingSessions:
    """/api/v1/training/sessions — depends on course"""

    async def _create_course(self, client: AsyncClient, token: str) -> dict:
        resp = await client.post(
            "/api/v1/training/courses",
            json={"code": "CRS-SES", "title": "Session Test", "modality": "online", "duration_hours": 8, "content": "Test"},
            headers=_auth(token),
        )
        return resp.json()

    async def test_create_session(self, client: AsyncClient, admin_token: str):
        course = await self._create_course(client, admin_token)
        resp = await client.post(
            "/api/v1/training/sessions",
            json={"course_id": course["id"], "instructor": "Prof A", "start_date": "2026-06-01", "end_date": "2026-06-05"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["instructor"] == "Prof A"
        assert body["status"] == "scheduled"

    async def test_list_sessions_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/sessions", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_sessions_after_create(self, client: AsyncClient, admin_token: str):
        course = await self._create_course(client, admin_token)
        await client.post(
            "/api/v1/training/sessions",
            json={"course_id": course["id"], "instructor": "Prof B", "start_date": "2026-07-01", "end_date": "2026-07-03"},
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/training/sessions", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["instructor"] == "Prof B"

    async def test_get_session_by_id(self, client: AsyncClient, admin_token: str):
        course = await self._create_course(client, admin_token)
        created = (await client.post(
            "/api/v1/training/sessions",
            json={"course_id": course["id"], "instructor": "Prof C", "start_date": "2026-08-01", "end_date": "2026-08-02"},
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/training/sessions/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_session_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/sessions/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_session(self, client: AsyncClient, admin_token: str):
        course = await self._create_course(client, admin_token)
        created = (await client.post(
            "/api/v1/training/sessions",
            json={"course_id": course["id"], "instructor": "Prof D", "start_date": "2026-09-01", "end_date": "2026-09-02"},
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/training/sessions/{created['id']}",
            json={"instructor": "Dr D"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["instructor"] == "Dr D"

    async def test_create_session_nonexistent_course(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/training/sessions",
            json={"course_id": 99999, "instructor": "Ghost", "start_date": "2026-10-01", "end_date": "2026-10-02"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestCertificationRecords:
    """/api/v1/training/certifications — depends on course"""

    async def _create_course(self, client: AsyncClient, token: str) -> dict:
        resp = await client.post(
            "/api/v1/training/courses",
            json={"code": "CRS-CERT", "title": "Cert Test", "modality": "online", "duration_hours": 40, "content": "Test"},
            headers=_auth(token),
        )
        return resp.json()

    async def test_create_certification(self, client: AsyncClient, admin_token: str):
        course = await self._create_course(client, admin_token)
        resp = await client.post(
            "/api/v1/training/certifications",
            json={"code": "CERT-001", "participant_name": "Maria R", "course_id": course["id"], "certificate_code": "CF-001"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "CERT-001"
        assert body["status"] == "active"

    async def test_list_certifications_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/certifications", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_certifications_after_create(self, client: AsyncClient, admin_token: str):
        course = await self._create_course(client, admin_token)
        await client.post(
            "/api/v1/training/certifications",
            json={"code": "CERT-002", "participant_name": "Juan P", "course_id": course["id"], "certificate_code": "CF-002"},
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/training/certifications", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["participant_name"] == "Juan P"

    async def test_get_certification_by_id(self, client: AsyncClient, admin_token: str):
        course = await self._create_course(client, admin_token)
        created = (await client.post(
            "/api/v1/training/certifications",
            json={"code": "CERT-003", "participant_name": "Ana L", "course_id": course["id"], "certificate_code": "CF-003"},
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/training/certifications/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_certification_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/certifications/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_certification(self, client: AsyncClient, admin_token: str):
        course = await self._create_course(client, admin_token)
        created = (await client.post(
            "/api/v1/training/certifications",
            json={"code": "CERT-004", "participant_name": "Luis M", "course_id": course["id"], "certificate_code": "CF-004"},
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/training/certifications/{created['id']}",
            json={"status": "expired"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "expired"

    async def test_create_certification_nonexistent_course(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/training/certifications",
            json={"code": "CERT-FAIL", "participant_name": "Ghost", "course_id": 99999, "certificate_code": "CF-FAIL"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404


class TestUserManuals:
    """/api/v1/training/manuals"""

    CREATE_PAYLOAD = {
        "code": "MAN-001",
        "title": "ERP User Guide",
        "product": "Mardtek ERP",
        "content_url": "https://docs.example.com/erp",
    }

    async def test_create_manual(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/training/manuals", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "MAN-001"
        assert body["version"] == "1.0"

    async def test_list_manuals_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/manuals", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_manuals_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/training/manuals", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/training/manuals", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "ERP User Guide"

    async def test_get_manual_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/manuals", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/training/manuals/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_manual_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/manuals/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_manual(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/manuals", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/training/manuals/{created['id']}",
            json={"title": "Updated Guide"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Guide"


class TestVideoTutorials:
    """/api/v1/training/video-tutorials"""

    CREATE_PAYLOAD = {
        "code": "VID-001",
        "title": "Getting Started",
        "url": "https://videos.example.com/start",
        "duration_minutes": 15,
    }

    async def test_create_video_tutorial(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/training/video-tutorials", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "VID-001"
        assert body["status"] == "draft"

    async def test_list_video_tutorials_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/video-tutorials", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_video_tutorials_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/training/video-tutorials", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/training/video-tutorials", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Getting Started"

    async def test_get_video_tutorial_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/video-tutorials", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/training/video-tutorials/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_video_tutorial_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/training/video-tutorials/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_video_tutorial(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/training/video-tutorials", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/training/video-tutorials/{created['id']}",
            json={"title": "Advanced Tutorial"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Advanced Tutorial"


class TestTrainingAuth:
    """Auth protection for Training Services endpoints."""

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
        resp = await client.get("/api/v1/training/needs")
        assert resp.status_code == 401

    async def test_viewer_cannot_delete_need(self, client: AsyncClient):
        token = await self._register_and_login(client, "trnviewer", "viewer")

        create = await client.post(
            "/api/v1/training/needs",
            json={"code": "TN-AUTH01", "employee_name": "Viewer User", "role": "Dev", "skills_gap": "Testing auth"},
            headers=_auth(token),
        )
        assert create.status_code == 201, create.text
        need_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/training/needs/{need_id}",
            headers=_auth(token),
        )
        assert resp.status_code == 405

    async def test_viewer_can_create_need(self, client: AsyncClient):
        token = await self._register_and_login(client, "trnviewer2", "viewer")
        resp = await client.post(
            "/api/v1/training/needs",
            json={"code": "TN-AUTH02", "employee_name": "Viewer Creates", "role": "Tester", "skills_gap": "Python"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
