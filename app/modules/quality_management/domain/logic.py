"""Business logic for P2 — Quality Management & Continuous Improvement."""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quality_management.domain.models import (
    ActionStatus,
    AuditStatus,
    CorrectiveAction,
    Document,
    DocumentStatus,
    ImprovementStatus,
    InternalAudit,
    NCStatus,
    NonConformity,
)


# ─── Document Logic ──────────────────────────────────────────────────────

async def approve_document(db: AsyncSession, document_id: int, approved_by: str) -> Optional[Document]:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        return None
    doc.status = DocumentStatus.APPROVED
    doc.approved_by = approved_by
    from datetime import datetime, timezone
    doc.approved_at = datetime.now(timezone.utc)
    await db.flush()
    return doc


async def get_expired_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(
        select(Document).where(
            Document.next_review_at.isnot(None),
            Document.next_review_at < date.today(),
            Document.status != DocumentStatus.OBSOLETE,
        )
    )
    return list(result.scalars().all())


# ─── Non-Conformity Logic ───────────────────────────────────────────────

async def close_nc(db: AsyncSession, nc_id: int) -> Optional[NonConformity]:
    """Close an NC only when all linked corrective actions are verified."""
    result = await db.execute(
        select(NonConformity).where(NonConformity.id == nc_id)
    )
    nc = result.scalar_one_or_none()
    if nc is None:
        return None

    # Check all corrective actions are verified
    action_result = await db.execute(
        select(CorrectiveAction).where(CorrectiveAction.nc_id == nc_id)
    )
    actions = list(action_result.scalars().all())
    if actions and any(a.status != ActionStatus.VERIFIED for a in actions):
        return None  # Cannot close — open actions remain

    from datetime import datetime, timezone
    nc.status = NCStatus.CLOSED
    nc.closed_at = datetime.now(timezone.utc)
    await db.flush()
    return nc


# ─── Corrective Action Logic ────────────────────────────────────────────

async def verify_action_effectiveness(
    db: AsyncSession, action_id: int, review: str
) -> Optional[CorrectiveAction]:
    result = await db.execute(
        select(CorrectiveAction).where(CorrectiveAction.id == action_id)
    )
    action = result.scalar_one_or_none()
    if action is None:
        return None
    action.status = ActionStatus.VERIFIED
    action.effectiveness_review = review
    await db.flush()
    return action


# ─── Audit Logic ─────────────────────────────────────────────────────────

async def complete_audit(
    db: AsyncSession,
    audit_id: int,
    findings_summary: str,
    result: str,
    report_url: Optional[str] = None,
) -> Optional[InternalAudit]:
    result_obj = await db.execute(select(InternalAudit).where(InternalAudit.id == audit_id))
    audit = result_obj.scalar_one_or_none()
    if audit is None:
        return None
    from datetime import date
    audit.status = AuditStatus.COMPLETED
    audit.audit_date = date.today()
    audit.findings_summary = findings_summary
    audit.result = result  # type: ignore[assignment]
    audit.report_url = report_url
    await db.flush()
    return audit
