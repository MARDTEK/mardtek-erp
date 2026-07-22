"""Business logic for P7 — HR Management."""

from __future__ import annotations

from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.human_resources.domain.models import (
    CompetencyAssessment,
    EvaluationStatus,
    PerformanceEvaluation,
    PersonnelRequest,
    PersonnelRequestStatus,
    StaffRegister,
    StaffStatus,
)


async def get_active_headcount(db: AsyncSession, department: str) -> int:
    """Return the number of active employees in a given department."""
    result = await db.execute(
        select(func.count(StaffRegister.id)).where(
            StaffRegister.department == department,
            StaffRegister.status == StaffStatus.ACTIVE,
        )
    )
    return result.scalar() or 0


async def get_turnover_rate(db: AsyncSession, year: int) -> float:
    """Calculate the turnover rate for a given year.

    Turnover rate = (terminations during year / average headcount) * 100.
    This is a simplified calculation; a real implementation would use
    hire/termination dates for accuracy.
    """
    total_count_result = await db.execute(select(func.count(StaffRegister.id)))
    total_count = total_count_result.scalar() or 0
    if total_count == 0:
        return 0.0

    terminated_count_result = await db.execute(
        select(func.count(StaffRegister.id)).where(
            StaffRegister.status == StaffStatus.TERMINATED,
        )
    )
    terminated_count = terminated_count_result.scalar() or 0

    if total_count == 0:
        return 0.0

    return round((terminated_count / total_count) * 100, 2)


async def get_employees_by_competency_gap(
    db: AsyncSession, skill: str
) -> List[StaffRegister]:
    """Return active employees who have a competency gap for a given skill."""
    result = await db.execute(
        select(StaffRegister)
        .join(CompetencyAssessment, CompetencyAssessment.employee_id == StaffRegister.id)
        .where(
            StaffRegister.status == StaffStatus.ACTIVE,
            CompetencyAssessment.skill == skill,
            CompetencyAssessment.has_gap == True,
        )
    )
    return list(result.scalars().all())


# ─── PersonnelRequest Transitions ──────────────────────────────────────────

async def transition_personnel_request(
    record: PersonnelRequest,
    target_status: str,
) -> PersonnelRequest:
    current = record.status
    target = PersonnelRequestStatus(target_status)

    valid: bool = False

    if current == PersonnelRequestStatus.OPEN and target == PersonnelRequestStatus.APPROVED:
        valid = True
    elif current == PersonnelRequestStatus.OPEN and target == PersonnelRequestStatus.REJECTED:
        valid = True
    elif current == PersonnelRequestStatus.APPROVED and target == PersonnelRequestStatus.FILLED:
        valid = True

    if not valid:
        raise ValueError(
            f"Cannot transition from {current.value} to {target.value}"
        )

    record.status = target
    return record


# ─── PerformanceEvaluation Transitions ─────────────────────────────────────

async def transition_evaluation_status(
    record: PerformanceEvaluation,
    target_status: str,
) -> PerformanceEvaluation:
    current = record.status
    target = EvaluationStatus(target_status)

    valid: bool = False

    if current == EvaluationStatus.DRAFT and target == EvaluationStatus.SUBMITTED:
        valid = True
    elif current == EvaluationStatus.SUBMITTED and target == EvaluationStatus.COMPLETED:
        valid = True

    if not valid:
        raise ValueError(
            f"Cannot transition from {current.value} to {target.value}"
        )

    record.status = target
    return record
