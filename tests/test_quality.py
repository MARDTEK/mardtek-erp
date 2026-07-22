"""Integration tests — Quality Management (P2) CRUD + business logic (with auth)."""

from httpx import AsyncClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestDocuments:
    """/api/v1/quality/documents"""

    CREATE_PAYLOAD = {
        "code": "SOP-P2-001-QM",
        "title": "Quality Manual",
        "process_code": "P2",
        "doc_type": "SOP",
        "next_review_at": "2027-01-01",
    }

    async def test_create_document(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "SOP-P2-001-QM"
        assert body["status"] == "draft"
        assert body["version"] == "1.0"

    async def test_list_documents_empty(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/quality/documents", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_documents_after_create(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/quality/documents", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Quality Manual"

    async def test_get_document_by_id(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.get(
            f"/api/v1/quality/documents/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_document_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/quality/documents/99999", headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_document(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/quality/documents/{created['id']}",
            json={"title": "Updated Manual"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Manual"

    async def test_filter_by_process_code(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        await client.post(
            "/api/v1/quality/documents", json={
                **self.CREATE_PAYLOAD,
                "code": "SOP-P1-001-STRAT",
                "process_code": "P1",
            },
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/quality/documents?process_code=P2",
            headers=_auth(admin_token),
        )
        data = resp.json()
        assert all(d["process_code"] == "P2" for d in data)

    async def test_delete_document(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/quality/documents", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/quality/documents/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 204

        get_resp = await client.get(
            f"/api/v1/quality/documents/{created['id']}",
            headers=_auth(admin_token),
        )
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

    async def test_create_nc(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "open"
        assert body["severity"] == "major"

    async def test_create_nc_invalid_severity(self, client: AsyncClient, admin_token: str):
        payload = {**self.CREATE_PAYLOAD, "code": "NC-2026-002", "severity": "unknown"}
        resp = await client.post(
            "/api/v1/quality/non-conformities", json=payload,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422

    async def test_list_ncs(self, client: AsyncClient, admin_token: str):
        await client.post(
            "/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )
        resp = await client.get(
            "/api/v1/quality/non-conformities", headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_close_nc(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.post(
            f"/api/v1/quality/non-conformities/{created['id']}/close",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    async def test_update_root_cause(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{created['id']}/root-cause",
            json={"root_cause": "Lack of training"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["root_cause"] == "Lack of training"

    async def test_transition_to_investigating(self, client: AsyncClient, admin_token: str):
        """OPEN → INVESTIGATING via explicit transition."""
        nc = (await client.post("/api/v1/quality/non-conformities", json={
            **self.CREATE_PAYLOAD, "code": "NC-2026-020",
        }, headers=_auth(admin_token))).json()
        assert nc["status"] == "open"

        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "investigating"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "investigating"

    async def test_transition_investigating_to_ca(self, client: AsyncClient, admin_token: str):
        """INVESTIGATING → CORRECTIVE_ACTION requires at least one CA."""
        nc = (await client.post("/api/v1/quality/non-conformities", json={
            **self.CREATE_PAYLOAD, "code": "NC-2026-021",
        }, headers=_auth(admin_token))).json()

        # Move to investigating
        await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "investigating"},
            headers=_auth(admin_token),
        )

        # Try transition to CA without any CA → should fail
        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "corrective_action"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 409

        # Create a CA
        await client.post("/api/v1/quality/corrective-actions", json={
            "code": "CA-2026-020",
            "nc_id": nc["id"],
            "description": "Test CA",
            "responsible": "tester",
            "deadline": "2026-10-01",
        }, headers=_auth(admin_token))

        # Now transition should work
        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "corrective_action"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "corrective_action"

    async def test_transition_ca_to_closed(self, client: AsyncClient, admin_token: str):
        """CORRECTIVE_ACTION → VERIFICATION → CLOSED full flow."""
        nc = (await client.post("/api/v1/quality/non-conformities", json={
            **self.CREATE_PAYLOAD, "code": "NC-2026-022",
        }, headers=_auth(admin_token))).json()

        # Move to investigating → CA
        await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "investigating"},
            headers=_auth(admin_token),
        )
        ca = (await client.post("/api/v1/quality/corrective-actions", json={
            "code": "CA-2026-022",
            "nc_id": nc["id"],
            "description": "Fix NC-022",
            "responsible": "tester",
            "deadline": "2026-10-01",
        }, headers=_auth(admin_token))).json()

        await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "corrective_action"},
            headers=_auth(admin_token),
        )

        # Try close without verify → should fail
        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "closed"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 409

        # Verify the CA
        await client.post(
            f"/api/v1/quality/corrective-actions/{ca['id']}/verify",
            json={"effectiveness_review": "Effective"},
            headers=_auth(admin_token),
        )

        # Transition to verification
        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "verification"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "verification"

        # Now close should work
        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "closed"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    async def test_transition_invalid_direct(self, client: AsyncClient, admin_token: str):
        """OPEN → CLOSED directly should be rejected."""
        nc = (await client.post("/api/v1/quality/non-conformities", json={
            **self.CREATE_PAYLOAD, "code": "NC-2026-023",
        }, headers=_auth(admin_token))).json()

        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "closed"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 409

    async def test_transition_nonexistent_nc(self, client: AsyncClient, admin_token: str):
        """Transition on non-existent NC → 404."""
        resp = await client.patch(
            "/api/v1/quality/non-conformities/99999/transition",
            json={"target_status": "investigating"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404

    async def test_transition_invalid_target_status(self, client: AsyncClient, admin_token: str):
        """Invalid target_status should be 422."""
        nc = (await client.post("/api/v1/quality/non-conformities", json={
            **self.CREATE_PAYLOAD, "code": "NC-2026-024",
        }, headers=_auth(admin_token))).json()

        resp = await client.patch(
            f"/api/v1/quality/non-conformities/{nc['id']}/transition",
            json={"target_status": "invalid"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422

    async def test_close_nc_direct_still_works(self, client: AsyncClient, admin_token: str):
        """The existing /close endpoint should still work (backward compat)."""
        nc = (await client.post("/api/v1/quality/non-conformities", json={
            **self.CREATE_PAYLOAD, "code": "NC-2026-025",
        }, headers=_auth(admin_token))).json()
        resp = await client.post(
            f"/api/v1/quality/non-conformities/{nc['id']}/close",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    async def test_delete_nc(self, client: AsyncClient, admin_token: str):
        created = (await client.post(
            "/api/v1/quality/non-conformities", json=self.CREATE_PAYLOAD,
            headers=_auth(admin_token),
        )).json()
        resp = await client.delete(
            f"/api/v1/quality/non-conformities/{created['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 204


class TestCorrectiveActions:
    """Full flow: create NC → create CA → verify CA → close NC."""

    async def test_full_corrective_action_flow(self, client: AsyncClient, admin_token: str):
        # 1. Create NC
        nc = (await client.post("/api/v1/quality/non-conformities", json={
            "code": "NC-2026-010",
            "source": "Audit", "description": "Finding #1", "severity": "minor",
            "reported_by": "auditor",
        }, headers=_auth(admin_token))).json()

        # 2. Create Corrective Action
        ca_resp = await client.post("/api/v1/quality/corrective-actions", json={
            "code": "CA-2026-001",
            "nc_id": nc["id"],
            "description": "Train staff on procedure",
            "responsible": "jdoe",
            "deadline": "2026-09-01",
        }, headers=_auth(admin_token))
        assert ca_resp.status_code == 201
        ca = ca_resp.json()

        # 3. Verify effectiveness
        verify_resp = await client.post(
            f"/api/v1/quality/corrective-actions/{ca['id']}/verify",
            json={"effectiveness_review": "Training completed and effective"},
            headers=_auth(admin_token),
        )
        assert verify_resp.status_code == 200
        assert verify_resp.json()["status"] == "verified"

        # 4. Close NC (now that CA is verified it should succeed)
        close_resp = await client.post(
            f"/api/v1/quality/non-conformities/{nc['id']}/close",
            headers=_auth(admin_token),
        )
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

    async def test_create_audit(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/quality/audits", json=self.CREATE_AUDIT,
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "planned"

    async def test_add_checklist_and_complete_audit(self, client: AsyncClient, admin_token: str):
        audit = (await client.post(
            "/api/v1/quality/audits", json=self.CREATE_AUDIT,
            headers=_auth(admin_token),
        )).json()
        aid = audit["id"]

        # Add checklist items
        items = []
        for q in ("Is documentation in place?", "Are records maintained?"):
            resp = await client.post(
                f"/api/v1/quality/audits/{aid}/checklist",
                json={"question": q},
                headers=_auth(admin_token),
            )
            assert resp.status_code == 201
            items.append(resp.json())

        # List checklist
        listing = (await client.get(
            f"/api/v1/quality/audits/{aid}/checklist",
            headers=_auth(admin_token),
        )).json()
        assert len(listing) == 2

        # Update one item — use the correct path (/api/v1/quality/checklist/{item_id})
        patch_resp = await client.patch(
            f"/api/v1/quality/checklist/{items[0]['id']}",
            json={"result": "pass", "evidence": "Docs verified"},
            headers=_auth(admin_token),
        )
        assert patch_resp.status_code == 200

        # Complete audit
        complete = await client.post(
            f"/api/v1/quality/audits/{aid}/complete",
            params={"findings_summary": "All good", "result": "pass", "report_url": "http://url"},
            headers=_auth(admin_token),
        )
        assert complete.status_code == 200
        assert complete.json()["status"] == "completed"


class TestProcessOwners:
    async def test_crud_flow(self, client: AsyncClient, admin_token: str):
        # Create
        resp = await client.post("/api/v1/quality/process-owners", json={
            "process_code": "P2",
            "process_name": "Quality Management",
            "owner_name": "John Doe",
            "role": "Quality Manager",
            "since_date": "2026-01-01",
        }, headers=_auth(admin_token))
        assert resp.status_code == 201
        po_id = resp.json()["id"]

        # List
        lst = (await client.get(
            "/api/v1/quality/process-owners", headers=_auth(admin_token),
        )).json()
        assert len(lst) == 1
        assert lst[0]["owner_name"] == "John Doe"

        # Delete
        del_resp = await client.delete(
            f"/api/v1/quality/process-owners/{po_id}",
            headers=_auth(admin_token),
        )
        assert del_resp.status_code == 204


class TestImprovements:
    async def test_crud(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/quality/improvements", json={
            "code": "CI-2026-001",
            "source": "Management Review",
            "description": "Implement digital signatures",
            "responsible": "jdoe",
        }, headers=_auth(admin_token))
        assert resp.status_code == 201
        imp_id = resp.json()["id"]

        items = (await client.get(
            "/api/v1/quality/improvements", headers=_auth(admin_token),
        )).json()
        assert len(items) == 1

        # Implement
        impl = await client.post(
            f"/api/v1/quality/improvements/{imp_id}/implement",
            headers=_auth(admin_token),
        )
        assert impl.status_code == 200
        assert impl.json()["status"] == "implemented"
