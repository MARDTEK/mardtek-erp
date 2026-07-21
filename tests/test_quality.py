"""Integration tests — Quality Management (P2) CRUD + business logic."""

from httpx import AsyncClient


class TestDocuments:
    """/api/v1/quality/documents"""

    CREATE_PAYLOAD = {
        "code": "SOP-P2-001-QM",
        "title": "Quality Manual",
        "process_code": "P2",
        "doc_type": "SOP",
        "next_review_at": "2027-01-01",
    }

    async def test_create_document(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "SOP-P2-001-QM"
        assert body["status"] == "draft"
        assert body["version"] == "1.0"

    async def test_list_documents_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/quality/documents")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_documents_after_create(self, client: AsyncClient):
        await client.post("/api/v1/quality/documents", json=self.CREATE_PAYLOAD)
        resp = await client.get("/api/v1/quality/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Quality Manual"

    async def test_get_document_by_id(self, client: AsyncClient):
        created = (await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD
        )).json()
        resp = await client.get(f"/api/v1/quality/documents/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_document_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/quality/documents/99999")
        assert resp.status_code == 404

    async def test_update_document(self, client: AsyncClient):
        created = (await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD
        )).json()
        resp = await client.patch(
            f"/api/v1/quality/documents/{created['id']}",
            json={"title": "Updated Manual"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Manual"

    async def test_filter_by_process_code(self, client: AsyncClient):
        await client.post("/api/v1/quality/documents", json=self.CREATE_PAYLOAD)
        await client.post("/api/v1/quality/documents", json={
            **self.CREATE_PAYLOAD,
            "code": "SOP-P1-001-STRAT",
            "process_code": "P1",
        })
        resp = await client.get("/api/v1/quality/documents?process_code=P2")
        data = resp.json()
        assert all(d["process_code"] == "P2" for d in data)

    async def test_delete_document(self, client: AsyncClient):
        created = (await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD
        )).json()
        resp = await client.delete(f"/api/v1/quality/documents/{created['id']}")
        assert resp.status_code == 204

        get_resp = await client.get(f"/api/v1/quality/documents/{created['id']}")
        assert get_resp.status_code == 404


class TestNonConformities:
    """/api/v1/quality/non-conformities"""

    CREATE_PAYLOAD = {
        "code": "NC-2026-001",
        "source": "Internal Audit",
        "source_ref": "AUDIT-2026-001",
        "description": "Missing signature on process record",
        "severity": "major",
        "reported_by": "jdoe",
    }

    async def test_create_nc(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "open"
        assert body["severity"] == "major"

    async def test_create_nc_invalid_severity(self, client: AsyncClient):
        payload = {**self.CREATE_PAYLOAD, "code": "NC-2026-002", "severity": "unknown"}
        resp = await client.post(
            "/api/v1/quality/non-conformities", json=payload
        )
        assert resp.status_code == 422

    async def test_list_ncs(self, client: AsyncClient):
        await client.post("/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD)
        resp = await client.get("/api/v1/quality/non-conformities")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_close_nc(self, client: AsyncClient):
        created = (await client.post(
            "/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD
        )).json()
        resp = await client.post(
            f"/api/v1/quality/non-conformities/{created['id']}/close"
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    async def test_update_root_cause(self, client: AsyncClient):
        created = (await client.post(
            "/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD
        )).json()
        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{created['id']}/root-cause",
            json={"root_cause": "Lack of training"},
        )
        assert resp.status_code == 200
        assert resp.json()["root_cause"] == "Lack of training"

    async def test_delete_nc(self, client: AsyncClient):
        created = (await client.post(
            "/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD
        )).json()
        resp = await client.delete(f"/api/v1/quality/non-conformities/{created['id']}")
        assert resp.status_code == 204


class TestCorrectiveActions:
    """Full flow: create NC → create CA → verify CA → close NC."""

    async def test_full_corrective_action_flow(self, client: AsyncClient):
        # 1. Create NC
        nc = (await client.post("/api/v1/quality/non-conformities", json={
            "code": "NC-2026-010",
            "source": "Audit", "description": "Finding #1", "severity": "minor",
            "reported_by": "auditor",
        })).json()

        # 2. Create Corrective Action
        ca_resp = await client.post("/api/v1/quality/corrective-actions", json={
            "code": "CA-2026-001",
            "nc_id": nc["id"],
            "description": "Train staff on procedure",
            "responsible": "jdoe",
            "deadline": "2026-09-01",
        })
        assert ca_resp.status_code == 201
        ca = ca_resp.json()

        # 3. Verify effectiveness
        verify_resp = await client.post(
            f"/api/v1/quality/corrective-actions/{ca['id']}/verify",
            json={"effectiveness_review": "Training completed and effective"},
        )
        assert verify_resp.status_code == 200
        assert verify_resp.json()["status"] == "verified"

        # 4. Close NC (now that CA is verified it should succeed)
        close_resp = await client.post(f"/api/v1/quality/non-conformities/{nc['id']}/close")
        assert close_resp.status_code == 200
        assert close_resp.json()["status"] == "closed"


class TestInternalAudits:
    """/api/v1/quality/audits + checklist items."""

    CREATE_AUDIT = {
        "code": "AUDIT-P2-2026-001",
        "scheduled_date": "2026-08-15",
        "scope": "Complete P2 audit",
        "auditor": "jsmith",
        "audited_process": "P2",
    }

    async def test_create_audit(self, client: AsyncClient):
        resp = await client.post("/api/v1/quality/audits", json=self.CREATE_AUDIT)
        assert resp.status_code == 201
        assert resp.json()["status"] == "planned"

    async def test_add_checklist_and_complete_audit(self, client: AsyncClient):
        audit = (await client.post(
            "/api/v1/quality/audits", json=self.CREATE_AUDIT
        )).json()
        aid = audit["id"]

        # Add checklist items
        for q in ("Is documentation in place?", "Are records maintained?"):
            resp = await client.post(
                f"/api/v1/quality/audits/{aid}/checklist",
                json={"question": q},
            )
            assert resp.status_code == 201

        # List checklist
        items = (await client.get(
            f"/api/v1/quality/audits/{aid}/checklist"
        )).json()
        assert len(items) == 2

        # Update one item
        await client.patch(
            f"/api/v1/quality/audits/{aid}/checklist/{items[0]['id']}",
            json={"result": "pass", "evidence": "Docs verified"},
        )

        # Complete audit
        complete = await client.post(
            f"/api/v1/quality/audits/{aid}/complete",
            params={"findings_summary": "All good", "result": "pass", "report_url": "http://url"},
        )
        assert complete.status_code == 200
        assert complete.json()["status"] == "completed"


class TestProcessOwners:
    async def test_crud_flow(self, client: AsyncClient):
        # Create
        resp = await client.post("/api/v1/quality/process-owners", json={
            "process_code": "P2",
            "process_name": "Quality Management",
            "owner_name": "John Doe",
            "role": "Quality Manager",
            "since_date": "2026-01-01",
        })
        assert resp.status_code == 201
        po_id = resp.json()["id"]

        # List
        lst = (await client.get("/api/v1/quality/process-owners")).json()
        assert len(lst) == 1
        assert lst[0]["owner_name"] == "John Doe"

        # Delete
        del_resp = await client.delete(f"/api/v1/quality/process-owners/{po_id}")
        assert del_resp.status_code == 204


class TestImprovements:
    async def test_crud(self, client: AsyncClient):
        resp = await client.post("/api/v1/quality/improvements", json={
            "code": "CI-2026-001",
            "source": "Management Review",
            "description": "Implement digital signatures",
            "responsible": "jdoe",
        })
        assert resp.status_code == 201
        imp_id = resp.json()["id"]

        items = (await client.get("/api/v1/quality/improvements")).json()
        assert len(items) == 1

        # Implement
        impl = await client.post(f"/api/v1/quality/improvements/{imp_id}/implement")
        assert impl.status_code == 200
        assert impl.json()["status"] == "implemented"
