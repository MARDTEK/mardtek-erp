from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quality_management.domain.models import (
    ActionStatus,
    AuditStatus,
    ContinuousImprovement,
    CorrectiveAction,
    Document,
    DocumentStatus,
    ImprovementStatus,
    InternalAudit,
    NCStatus,
    NonConformity,
)


class QualityService:
    @staticmethod
    async def approve_document(db: AsyncSession, document_id: int, approved_by: str) -> Optional[Document]:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if doc is None:
            return None
        doc.status = DocumentStatus.APPROVED
        doc.approved_by = approved_by
        doc.approved_at = datetime.now(timezone.utc)
        await db.flush()
        return doc

    @staticmethod
    async def get_expired_documents(db: AsyncSession) -> list[Document]:
        result = await db.execute(
            select(Document).where(
                Document.next_review_at.isnot(None),
                Document.next_review_at < date.today(),
                Document.status != DocumentStatus.OBSOLETE,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def close_nc(db: AsyncSession, nc_id: int) -> Optional[NonConformity]:
        result = await db.execute(
            select(NonConformity).where(NonConformity.id == nc_id)
        )
        nc = result.scalar_one_or_none()
        if nc is None:
            return None

        action_result = await db.execute(
            select(CorrectiveAction).where(CorrectiveAction.nc_id == nc_id)
        )
        actions = list(action_result.scalars().all())
        if actions and any(a.status != ActionStatus.VERIFIED for a in actions):
            return None

        nc.status = NCStatus.CLOSED
        nc.closed_at = datetime.now(timezone.utc)
        await db.flush()
        return nc

    @staticmethod
    async def transition_nc_status(
        db: AsyncSession, nc_id: int, target_status: str
    ) -> Optional[NonConformity]:
        result = await db.execute(
            select(NonConformity).where(NonConformity.id == nc_id)
        )
        nc = result.scalar_one_or_none()
        if nc is None:
            return None

        if nc.status.value == target_status:
            return nc

        if nc.status == NCStatus.OPEN and target_status == "investigating":
            nc.status = NCStatus.INVESTIGATING

        elif nc.status == NCStatus.INVESTIGATING and target_status == "corrective_action":
            ca_result = await db.execute(
                select(CorrectiveAction).where(CorrectiveAction.nc_id == nc_id)
            )
            actions = list(ca_result.scalars().all())
            if not actions:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot transition: no corrective actions defined for this NC",
                )
            nc.status = NCStatus.CORRECTIVE_ACTION

        elif nc.status == NCStatus.CORRECTIVE_ACTION and target_status == "verification":
            ca_result = await db.execute(
                select(CorrectiveAction).where(CorrectiveAction.nc_id == nc_id)
            )
            actions = list(ca_result.scalars().all())
            if actions and any(a.status != ActionStatus.VERIFIED for a in actions):
                raise HTTPException(
                    status_code=409,
                    detail="Cannot transition: not all corrective actions are verified",
                )
            nc.status = NCStatus.VERIFICATION

        elif nc.status == NCStatus.VERIFICATION and target_status == "closed":
            nc.status = NCStatus.CLOSED
            nc.closed_at = datetime.now(timezone.utc)

        else:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot transition from {nc.status.value} to {target_status}",
            )

        await db.flush()
        return nc

    @staticmethod
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

    @staticmethod
    async def complete_audit(
        db: AsyncSession,
        audit_id: int,
        findings_summary: str,
        result_value: str,
        report_url: Optional[str] = None,
    ) -> Optional[InternalAudit]:
        result_obj = await db.execute(select(InternalAudit).where(InternalAudit.id == audit_id))
        audit = result_obj.scalar_one_or_none()
        if audit is None:
            return None
        audit.status = AuditStatus.COMPLETED
        audit.audit_date = date.today()
        audit.findings_summary = findings_summary
        audit.result = result_value  # type: ignore[assignment]
        audit.report_url = report_url
        await db.flush()
        return audit

    @staticmethod
    async def implement_improvement(
        db: AsyncSession, improvement_id: int
    ) -> Optional[ContinuousImprovement]:
        result = await db.execute(
            select(ContinuousImprovement).where(ContinuousImprovement.id == improvement_id)
        )
        imp = result.scalar_one_or_none()
        if imp is None:
            return None
        imp.status = ImprovementStatus.IMPLEMENTED
        imp.implemented_at = datetime.now(timezone.utc)
        await db.flush()
        return imp

quality_service = QualityService()
