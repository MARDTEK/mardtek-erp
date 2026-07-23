from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.strategic_planning.domain.models import (
    ManagementReviewReport,
    QmsScope,
    QualityObjective,
)
from app.modules.strategic_planning.infrastructure.repositories import (
    management_review_repo,
    objective_repo,
    qms_scope_repo,
)


class StrategicService:
    @staticmethod
    def calculate_objective_progress(objective: QualityObjective) -> float:
        if objective.target_value <= 0:
            return 0.0
        if objective.actual_value is None:
            return 0.0
        progress = (objective.actual_value / objective.target_value) * 100.0
        return min(progress, 100.0)

    @staticmethod
    async def get_objectives_by_process(
        db: AsyncSession, process_code: str
    ) -> list[QualityObjective]:
        # Complex queries stay here or in a specialized repo method.
        # For simplicity, using SQLAlchemy directly here as before.
        result = await db.execute(
            select(QualityObjective)
            .where(QualityObjective.process_code == process_code)
            .order_by(QualityObjective.code)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_qms_scope(db: AsyncSession) -> Optional[QmsScope]:
        result = await db.execute(
            select(QmsScope).where(QmsScope.is_current.is_(True))
        )
        return result.scalar_one_or_none()

    @staticmethod
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
        management_review_repo.add(db, report)
        await db.flush()
        return report

strategic_service = StrategicService()
