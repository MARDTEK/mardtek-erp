from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.quality_management.domain.logic import (
    approve_document,
    close_nc,
    complete_audit,
    get_expired_documents,
    implement_improvement,
    verify_action_effectiveness,
)
from app.modules.quality_management.domain.models import (
    AuditChecklistItem,
    ContinuousImprovement,
    CorrectiveAction,
    Document,
    InternalAudit,
    NonConformity,
    ProcessOwner,
)
from app.modules.quality_management.schemas.dto import (
    AuditCreate,
    AuditResponse,
    ChecklistItemCreate,
    ChecklistItemResponse,
    ChecklistItemUpdate,
    CorrectiveActionCreate,
    CorrectiveActionResponse,
    CorrectiveActionVerify,
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    ImprovementCreate,
    ImprovementResponse,
    NCCreate,
    NCResponse,
    NCUpdateRootCause,
    ProcessOwnerCreate,
    ProcessOwnerResponse,
)

router = APIRouter()


# ─── Documents ───────────────────────────────────────────────────────────

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    process_code: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Document)
    if process_code:
        stmt = stmt.where(Document.process_code == process_code)
    if status:
        stmt = stmt.where(Document.status == status)
    result = await db.execute(stmt.order_by(Document.code))
    return list(result.scalars().all())


@router.get("/documents/expired", response_model=List[DocumentResponse])
async def list_expired_documents(db: AsyncSession = Depends(get_db)):
    return await get_expired_documents(db)


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(payload: DocumentCreate, db: AsyncSession = Depends(get_db)):
    doc = Document(**payload.model_dump())
    db.add(doc)
    await db.flush()
    return doc


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.patch("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: int, payload: DocumentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    await db.flush()
    return doc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.flush()


@router.post("/documents/{document_id}/approve", response_model=DocumentResponse)
async def approve_document_endpoint(
    document_id: int,
    approved_by: str,
    db: AsyncSession = Depends(get_db),
):
    doc = await approve_document(db, document_id, approved_by)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


# ─── Non-Conformities ────────────────────────────────────────────────────

@router.get("/non-conformities", response_model=List[NCResponse])
async def list_non_conformities(
    status_filter: str | None = None,
    severity: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NonConformity)
    if status_filter:
        stmt = stmt.where(NonConformity.status == status_filter)
    if severity:
        stmt = stmt.where(NonConformity.severity == severity)
    result = await db.execute(stmt.order_by(NonConformity.code.desc()))
    return list(result.scalars().all())


@router.post("/non-conformities", response_model=NCResponse, status_code=status.HTTP_201_CREATED)
async def create_non_conformity(payload: NCCreate, db: AsyncSession = Depends(get_db)):
    nc = NonConformity(**payload.model_dump())
    db.add(nc)
    await db.flush()
    return nc


@router.get("/non-conformities/{nc_id}", response_model=NCResponse)
async def get_non_conformity(nc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NonConformity).where(NonConformity.id == nc_id))
    nc = result.scalar_one_or_none()
    if not nc:
        raise HTTPException(status_code=404, detail="Non-conformity not found")
    return nc


@router.patch("/non-conformities/{nc_id}/root-cause", response_model=NCResponse)
async def update_root_cause(nc_id: int, payload: NCUpdateRootCause, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NonConformity).where(NonConformity.id == nc_id))
    nc = result.scalar_one_or_none()
    if not nc:
        raise HTTPException(status_code=404, detail="Non-conformity not found")
    nc.root_cause = payload.root_cause
    nc.status = "investigating"
    await db.flush()
    return nc


@router.post("/non-conformities/{nc_id}/close", response_model=NCResponse)
async def close_non_conformity(nc_id: int, db: AsyncSession = Depends(get_db)):
    nc = await close_nc(db, nc_id)
    if not nc:
        raise HTTPException(
            status_code=409,
            detail="Cannot close: pending corrective actions or NC not found",
        )
    return nc


@router.delete("/non-conformities/{nc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_non_conformity(nc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NonConformity).where(NonConformity.id == nc_id))
    nc = result.scalar_one_or_none()
    if not nc:
        raise HTTPException(status_code=404, detail="Non-conformity not found")
    await db.delete(nc)
    await db.flush()


# ─── Corrective Actions ──────────────────────────────────────────────────

@router.get("/corrective-actions", response_model=List[CorrectiveActionResponse])
async def list_corrective_actions(
    nc_id: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CorrectiveAction)
    if nc_id:
        stmt = stmt.where(CorrectiveAction.nc_id == nc_id)
    if status_filter:
        stmt = stmt.where(CorrectiveAction.status == status_filter)
    result = await db.execute(stmt.order_by(CorrectiveAction.code))
    return list(result.scalars().all())


@router.post("/corrective-actions", response_model=CorrectiveActionResponse, status_code=status.HTTP_201_CREATED)
async def create_corrective_action(payload: CorrectiveActionCreate, db: AsyncSession = Depends(get_db)):
    # Verify NC exists
    nc_result = await db.execute(select(NonConformity).where(NonConformity.id == payload.nc_id))
    if not nc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Non-conformity not found")

    action = CorrectiveAction(**payload.model_dump())
    db.add(action)

    # Auto-update NC status
    nc_result = await db.execute(select(NonConformity).where(NonConformity.id == payload.nc_id))
    nc = nc_result.scalar_one()
    nc.status = "corrective_action"

    await db.flush()
    return action


@router.get("/corrective-actions/{action_id}", response_model=CorrectiveActionResponse)
async def get_corrective_action(action_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CorrectiveAction).where(CorrectiveAction.id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    return action


@router.post("/corrective-actions/{action_id}/verify", response_model=CorrectiveActionResponse)
async def verify_corrective_action(
    action_id: int,
    payload: CorrectiveActionVerify,
    db: AsyncSession = Depends(get_db),
):
    action = await verify_action_effectiveness(db, action_id, payload.effectiveness_review)
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    return action


# ─── Internal Audits ─────────────────────────────────────────────────────

@router.get("/audits", response_model=List[AuditResponse])
async def list_audits(
    process_code: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(InternalAudit)
    if process_code:
        stmt = stmt.where(InternalAudit.audited_process == process_code)
    if status_filter:
        stmt = stmt.where(InternalAudit.status == status_filter)
    result = await db.execute(stmt.order_by(InternalAudit.scheduled_date.desc()))
    return list(result.scalars().all())


@router.post("/audits", response_model=AuditResponse, status_code=status.HTTP_201_CREATED)
async def create_audit(payload: AuditCreate, db: AsyncSession = Depends(get_db)):
    audit = InternalAudit(**payload.model_dump())
    db.add(audit)
    await db.flush()
    return audit


@router.get("/audits/{audit_id}", response_model=AuditResponse)
async def get_audit(audit_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InternalAudit).where(InternalAudit.id == audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


@router.post("/audits/{audit_id}/complete", response_model=AuditResponse)
async def complete_audit_endpoint(
    audit_id: int,
    findings_summary: str,
    result: str,
    report_url: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    audit = await complete_audit(db, audit_id, findings_summary, result, report_url)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


# ─── Audit Checklist ─────────────────────────────────────────────────────

@router.get("/audits/{audit_id}/checklist", response_model=List[ChecklistItemResponse])
async def list_checklist(audit_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditChecklistItem).where(AuditChecklistItem.audit_id == audit_id)
    )
    return list(result.scalars().all())


@router.post(
    "/audits/{audit_id}/checklist",
    response_model=ChecklistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_checklist_item(
    audit_id: int,
    payload: ChecklistItemCreate,
    db: AsyncSession = Depends(get_db),
):
    item = AuditChecklistItem(audit_id=audit_id, **payload.model_dump())
    db.add(item)
    await db.flush()
    return item


@router.patch("/checklist/{item_id}", response_model=ChecklistItemResponse)
async def update_checklist_item(item_id: int, payload: ChecklistItemUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditChecklistItem).where(AuditChecklistItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    return item


# ─── Process Owners ──────────────────────────────────────────────────────

@router.get("/process-owners", response_model=List[ProcessOwnerResponse])
async def list_process_owners(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProcessOwner).order_by(ProcessOwner.process_code))
    return list(result.scalars().all())


@router.post("/process-owners", response_model=ProcessOwnerResponse, status_code=status.HTTP_201_CREATED)
async def create_process_owner(payload: ProcessOwnerCreate, db: AsyncSession = Depends(get_db)):
    owner = ProcessOwner(**payload.model_dump())
    db.add(owner)
    await db.flush()
    return owner


@router.get("/process-owners/{process_code}", response_model=ProcessOwnerResponse)
async def get_process_owner(process_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProcessOwner).where(ProcessOwner.process_code == process_code)
    )
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="Process owner not found")
    return owner


@router.delete("/process-owners/{owner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_process_owner(owner_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProcessOwner).where(ProcessOwner.id == owner_id))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="Process owner not found")
    await db.delete(owner)
    await db.flush()


# ─── Continuous Improvement ──────────────────────────────────────────────

@router.get("/improvements", response_model=List[ImprovementResponse])
async def list_improvements(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ContinuousImprovement)
    if status_filter:
        stmt = stmt.where(ContinuousImprovement.status == status_filter)
    result = await db.execute(stmt.order_by(ContinuousImprovement.code.desc()))
    return list(result.scalars().all())


@router.post("/improvements", response_model=ImprovementResponse, status_code=status.HTTP_201_CREATED)
async def create_improvement(payload: ImprovementCreate, db: AsyncSession = Depends(get_db)):
    imp = ContinuousImprovement(**payload.model_dump())
    db.add(imp)
    await db.flush()
    return imp


@router.get("/improvements/{improvement_id}", response_model=ImprovementResponse)
async def get_improvement(improvement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContinuousImprovement).where(ContinuousImprovement.id == improvement_id)
    )
    imp = result.scalar_one_or_none()
    if not imp:
        raise HTTPException(status_code=404, detail="Improvement not found")
    return imp


@router.post("/improvements/{improvement_id}/implement", response_model=ImprovementResponse)
async def implement_improvement_endpoint(
    improvement_id: int,
    db: AsyncSession = Depends(get_db),
):
    imp = await implement_improvement(db, improvement_id)
    if not imp:
        raise HTTPException(status_code=404, detail="Improvement not found")
    return imp
