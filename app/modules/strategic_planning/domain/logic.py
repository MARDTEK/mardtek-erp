"""Business logic for P1 — Strategic Management & Planning."""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.strategic_planning.domain.models import (
    ManagementReviewReport,
    ObjectiveStatus,
    QmsScope,
    QualityObjective,
)


# ─── Objective Logic ────────────────────────────────────────────────────

def calculate_objective_progress(objective: QualityObjective) -> float:
    """Compute percentage progress toward the target value.

    Returns 0.0 if there is no actual_value yet, 100.0 if actual_value
    meets or exceeds target_value, or the proportion otherwise.
    """
    if objective.target_value <= 0:
        return 0.0
    if objective.actual_value is None:
        return 0.0
    progress = (objective.actual_value / objective.target_value) * 100.0
    return min(progress, 100.0)


async def get_objectives_by_process(
    db: AsyncSession, process_code: str
) -> list[QualityObjective]:
    """Return all quality objectives for a given process code (P1–P11)."""
    result = await db.execute(
        select(QualityObjective)
        .where(QualityObjective.process_code == process_code)
        .order_by(QualityObjective.code)
    )
    return list(result.scalars().all())


# ─── QMS Scope Logic ────────────────────────────────────────────────────

async def get_active_qms_scope(db: AsyncSession) -> Optional[QmsScope]:
    """Retrieve the currently active (is_current=True) QMS scope."""
    result = await db.execute(
        select(QmsScope).where(QmsScope.is_current.is_(True))
    )
    return result.scalar_one_or_none()


# ─── Management Review Logic ────────────────────────────────────────────

async def create_management_review_report(
    db: AsyncSession,
    code: str,
    title: str,
    review_period_start: date,
    review_period_end: date,
    prepared_by: str,
    summary: str,
    conclusions: Optional[dict] = None,
    report_url: Optional[str] = None,
) -> ManagementReviewReport:
    """Assemble and persist a management review report.

    Gathers context from quality objectives status, but the actual
    conclusions and NC/audit data is passed explicitly from the caller.
    """
    report = ManagementReviewReport(
        code=code,
        title=title,
        review_period_start=review_period_start,
        review_period_end=review_period_end,
        prepared_by=prepared_by,
        summary=summary,
        conclusions=conclusions or {},
        report_url=report_url,
    )
    db.add(report)
    await db.flush()
    return report
