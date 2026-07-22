"""Web routes for Quality Management — Documents, NCs, CAs, Audits, Improvements."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.quality_management.domain.models import (
    ContinuousImprovement,
    CorrectiveAction,
    Document,
    InternalAudit,
    NonConformity,
)
from app.web.deps import get_current_user_from_session
from app.web.utils import render

router = APIRouter(prefix="/quality", tags=["Web — Quality Management"])

_PER_PAGE = 20


# ─── Root redirect ────────────────────────────────────────────────────────


@router.get("", include_in_schema=False)
async def quality_root():
    """Sidebar links to /quality — redirect to documents list."""
    return _redirect("/quality/documents")


# ─── Helpers ──────────────────────────────────────────────────────────────


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


# ─── Documents ────────────────────────────────────────────────────────────


@router.get("/documents")
async def list_documents(
    request: Request,
    page: int = 1,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Document)
    if search:
        stmt = stmt.where(or_(Document.code.ilike(f"%{search}%"), Document.title.ilike(f"%{search}%")))

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(Document.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    documents = list(result.scalars().all())

    return render(request, "pages/quality/documents.html", {
        "documents": documents,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "page_title": "Documents",
    })


@router.get("/documents/table")
async def documents_table(
    request: Request,
    page: int = 1,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Document)
    if search:
        stmt = stmt.where(or_(Document.code.ilike(f"%{search}%"), Document.title.ilike(f"%{search}%")))

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(Document.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    documents = list(result.scalars().all())

    return render(request, "partials/quality/documents_table.html", {
        "documents": documents,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
    })


@router.get("/documents/{doc_id}")
async def document_detail(
    request: Request,
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        return _redirect("/quality/documents")
    return render(request, "pages/quality/document_detail.html", {
        "doc": doc,
        "page_title": f"Document {doc.code}",
    })


@router.post("/documents")
async def create_document(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    process_code: str = Form(...),
    doc_type: str = Form(...),
    file_path: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    doc = Document(
        code=code,
        title=title,
        process_code=process_code,
        doc_type=doc_type,
        file_path=file_path or None,
    )
    db.add(doc)
    await db.commit()
    return _redirect("/quality/documents")


@router.post("/documents/{doc_id}/edit")
async def edit_document(
    request: Request,
    doc_id: int,
    title: str = Form(...),
    file_path: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        return _redirect("/quality/documents")
    doc.title = title
    doc.file_path = file_path or None
    doc.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return _redirect(f"/quality/documents/{doc_id}")


@router.post("/documents/{doc_id}/delete")
async def delete_document(
    request: Request,
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if doc:
        doc.is_deleted = True
        doc.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/quality/documents")


@router.post("/documents/{doc_id}/approve")
async def approve_document(
    request: Request,
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if doc:
        doc.status = "approved"
        doc.approved_by = user.username
        doc.approved_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/quality/documents/{doc_id}")


# ─── Non-Conformities ────────────────────────────────────────────────────


@router.get("/non-conformities")
async def list_ncs(
    request: Request,
    page: int = 1,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(NonConformity)
    if search:
        stmt = stmt.where(or_(NonConformity.code.ilike(f"%{search}%"), NonConformity.description.ilike(f"%{search}%")))

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(NonConformity.code.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    ncs = list(result.scalars().all())

    return render(request, "pages/quality/non_conformities.html", {
        "ncs": ncs,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "page_title": "Non-Conformities",
    })


@router.get("/non-conformities/table")
async def nc_table(
    request: Request,
    page: int = 1,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(NonConformity)
    if search:
        stmt = stmt.where(or_(NonConformity.code.ilike(f"%{search}%"), NonConformity.description.ilike(f"%{search}%")))

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(NonConformity.code.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    ncs = list(result.scalars().all())

    return render(request, "partials/quality/nc_table.html", {
        "ncs": ncs,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
    })


@router.get("/non-conformities/{nc_id}")
async def nc_detail(
    request: Request,
    nc_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(NonConformity).where(NonConformity.id == nc_id))
    nc = result.scalar_one_or_none()
    if not nc:
        return _redirect("/quality/non-conformities")
    return render(request, "pages/quality/nc_detail.html", {
        "nc": nc,
        "page_title": f"NC {nc.code}",
    })


@router.post("/non-conformities")
async def create_nc(
    request: Request,
    code: str = Form(...),
    source: str = Form(...),
    description: str = Form(...),
    severity: str = Form(...),
    reported_by: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    nc = NonConformity(
        code=code, source=source, description=description,
        severity=severity, reported_by=reported_by,
    )
    db.add(nc)
    await db.commit()
    return _redirect("/quality/non-conformities")


@router.post("/non-conformities/{nc_id}/edit")
async def edit_nc(
    request: Request,
    nc_id: int,
    root_cause: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(NonConformity).where(NonConformity.id == nc_id))
    nc = result.scalar_one_or_none()
    if not nc:
        return _redirect("/quality/non-conformities")
    nc.root_cause = root_cause or None
    await db.commit()
    return _redirect(f"/quality/non-conformities/{nc_id}")


@router.post("/non-conformities/{nc_id}/transition")
async def transition_nc(
    request: Request,
    nc_id: int,
    target_status: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(NonConformity).where(NonConformity.id == nc_id))
    nc = result.scalar_one_or_none()
    if nc:
        nc.status = target_status
        if target_status == "closed":
            nc.closed_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/quality/non-conformities/{nc_id}")


@router.post("/non-conformities/{nc_id}/delete")
async def delete_nc(
    request: Request,
    nc_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(NonConformity).where(NonConformity.id == nc_id))
    nc = result.scalar_one_or_none()
    if nc:
        nc.is_deleted = True
        nc.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/quality/non-conformities")


# ─── Corrective Actions ──────────────────────────────────────────────────


@router.get("/corrective-actions")
async def list_cas(
    request: Request,
    page: int = 1,
    nc_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(CorrectiveAction)
    if nc_id:
        stmt = stmt.where(CorrectiveAction.nc_id == nc_id)

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(CorrectiveAction.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    actions = list(result.scalars().all())

    return render(request, "pages/quality/corrective_actions.html", {
        "actions": actions,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "nc_id": nc_id,
        "page_title": "Corrective Actions",
    })


@router.get("/corrective-actions/table")
async def ca_table(
    request: Request,
    page: int = 1,
    nc_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(CorrectiveAction)
    if nc_id:
        stmt = stmt.where(CorrectiveAction.nc_id == nc_id)

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(CorrectiveAction.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    actions = list(result.scalars().all())

    return render(request, "partials/quality/ca_table.html", {
        "actions": actions,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    })


@router.get("/corrective-actions/{action_id}")
async def ca_detail(
    request: Request,
    action_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(CorrectiveAction).where(CorrectiveAction.id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        return _redirect("/quality/corrective-actions")
    return render(request, "pages/quality/ca_detail.html", {
        "action": action,
        "page_title": f"CA {action.code}",
    })


@router.post("/corrective-actions")
async def create_ca(
    request: Request,
    code: str = Form(...),
    nc_id: int = Form(...),
    description: str = Form(...),
    responsible: str = Form(...),
    deadline: date = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    action = CorrectiveAction(
        code=code, nc_id=nc_id, description=description,
        responsible=responsible, deadline=deadline,
    )
    db.add(action)
    await db.commit()
    return _redirect("/quality/corrective-actions")


@router.post("/corrective-actions/{action_id}/verify")
async def verify_ca(
    request: Request,
    action_id: int,
    effectiveness_review: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(CorrectiveAction).where(CorrectiveAction.id == action_id))
    action = result.scalar_one_or_none()
    if action:
        action.effectiveness_review = effectiveness_review
        action.status = "verified"
        action.completed_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/quality/corrective-actions/{action_id}")


@router.post("/corrective-actions/{action_id}/delete")
async def delete_ca(
    request: Request,
    action_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(CorrectiveAction).where(CorrectiveAction.id == action_id))
    action = result.scalar_one_or_none()
    if action:
        action.is_deleted = True
        action.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/quality/corrective-actions")


# ─── Audits ───────────────────────────────────────────────────────────────


@router.get("/audits")
async def list_audits(
    request: Request,
    page: int = 1,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(InternalAudit)
    if search:
        stmt = stmt.where(or_(InternalAudit.code.ilike(f"%{search}%"), InternalAudit.scope.ilike(f"%{search}%")))

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(InternalAudit.scheduled_date.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    audits = list(result.scalars().all())

    return render(request, "pages/quality/audits.html", {
        "audits": audits,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "page_title": "Internal Audits",
    })


@router.get("/audits/table")
async def audits_table(
    request: Request,
    page: int = 1,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(InternalAudit)
    if search:
        stmt = stmt.where(or_(InternalAudit.code.ilike(f"%{search}%"), InternalAudit.scope.ilike(f"%{search}%")))

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(InternalAudit.scheduled_date.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    audits = list(result.scalars().all())

    return render(request, "partials/quality/audits_table.html", {
        "audits": audits,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
    })


@router.get("/audits/{audit_id}")
async def audit_detail(
    request: Request,
    audit_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(InternalAudit).where(InternalAudit.id == audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        return _redirect("/quality/audits")
    return render(request, "pages/quality/audit_detail.html", {
        "audit": audit,
        "page_title": f"Audit {audit.code}",
    })


@router.post("/audits")
async def create_audit(
    request: Request,
    code: str = Form(...),
    scheduled_date: date = Form(...),
    scope: str = Form(...),
    auditor: str = Form(...),
    audited_process: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    audit = InternalAudit(
        code=code, scheduled_date=scheduled_date, scope=scope,
        auditor=auditor, audited_process=audited_process,
    )
    db.add(audit)
    await db.commit()
    return _redirect("/quality/audits")


@router.post("/audits/{audit_id}/complete")
async def complete_audit(
    request: Request,
    audit_id: int,
    findings_summary: str = Form(...),
    result_val: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(InternalAudit).where(InternalAudit.id == audit_id))
    audit = result.scalar_one_or_none()
    if audit:
        audit.status = "completed"
        audit.result = result_val
        audit.findings_summary = findings_summary
        audit.audit_date = date.today()
        await db.commit()
    return _redirect(f"/quality/audits/{audit_id}")


@router.post("/audits/{audit_id}/delete")
async def delete_audit(
    request: Request,
    audit_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(InternalAudit).where(InternalAudit.id == audit_id))
    audit = result.scalar_one_or_none()
    if audit:
        audit.is_deleted = True
        audit.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/quality/audits")


# ─── Improvements ─────────────────────────────────────────────────────────


@router.get("/improvements")
async def list_improvements(
    request: Request,
    page: int = 1,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(ContinuousImprovement)
    if search:
        stmt = stmt.where(or_(
            ContinuousImprovement.code.ilike(f"%{search}%"),
            ContinuousImprovement.description.ilike(f"%{search}%"),
        ))

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(ContinuousImprovement.code.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    improvements = list(result.scalars().all())

    return render(request, "pages/quality/improvements.html", {
        "improvements": improvements,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "page_title": "Continuous Improvement",
    })


@router.get("/improvements/table")
async def improvements_table(
    request: Request,
    page: int = 1,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(ContinuousImprovement)
    if search:
        stmt = stmt.where(or_(
            ContinuousImprovement.code.ilike(f"%{search}%"),
            ContinuousImprovement.description.ilike(f"%{search}%"),
        ))

    count_r = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(ContinuousImprovement.code.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    improvements = list(result.scalars().all())

    return render(request, "partials/quality/improvements_table.html", {
        "improvements": improvements,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
    })


@router.get("/improvements/{improv_id}")
async def improvement_detail(
    request: Request,
    improv_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ContinuousImprovement).where(ContinuousImprovement.id == improv_id))
    imp = result.scalar_one_or_none()
    if not imp:
        return _redirect("/quality/improvements")
    return render(request, "pages/quality/improvement_detail.html", {
        "imp": imp,
        "page_title": f"Improvement {imp.code}",
    })


@router.post("/improvements")
async def create_improvement(
    request: Request,
    code: str = Form(...),
    source: str = Form(...),
    description: str = Form(...),
    expected_benefit: str = Form(""),
    responsible: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    imp = ContinuousImprovement(
        code=code, source=source, description=description,
        expected_benefit=expected_benefit or None, responsible=responsible,
    )
    db.add(imp)
    await db.commit()
    return _redirect("/quality/improvements")


@router.post("/improvements/{improv_id}/implement")
async def implement_improvement(
    request: Request,
    improv_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ContinuousImprovement).where(ContinuousImprovement.id == improv_id))
    imp = result.scalar_one_or_none()
    if imp:
        imp.status = "implemented"
        imp.implemented_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/quality/improvements/{improv_id}")


@router.post("/improvements/{improv_id}/delete")
async def delete_improvement(
    request: Request,
    improv_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ContinuousImprovement).where(ContinuousImprovement.id == improv_id))
    imp = result.scalar_one_or_none()
    if imp:
        imp.is_deleted = True
        imp.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/quality/improvements")
