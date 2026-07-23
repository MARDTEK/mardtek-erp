from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tech_development.domain.models import (
    DeploymentRecord,
    QATestReport,
    ReleaseStatus,
)
from app.modules.tech_development.infrastructure.repositories import (
    deployment_record_repo,
    release_plan_repo,
    roadmap_repo,
)


class TechDevelopmentService:
    @staticmethod
    def calculate_qa_pass_rate(report: QATestReport) -> float:
        """Return the pass rate as a float percentage (0–100)."""
        if report.total_tests == 0:
            return 0.0
        return round((report.passed / report.total_tests) * 100, 2)

    @staticmethod
    async def get_release_by_status(db: AsyncSession, status: str) -> list:
        """Return all release plans filtered by status string value."""
        return await release_plan_repo.get_by_status(db, status)

    @staticmethod
    async def get_active_roadmap_items(db: AsyncSession, product_line: str) -> list:
        """Return published roadmaps for a given product line, newest first."""
        return await roadmap_repo.get_active_by_product_line(db, product_line)

    @staticmethod
    async def create_deployment_record(
        db: AsyncSession,
        code: str,
        environment: str,
        deployed_by: str,
        release_id: int | None = None,
        status: str = "success",
        notes: str | None = None,
    ) -> DeploymentRecord:
        """Create and persist a deployment record."""
        record = DeploymentRecord(
            code=code,
            release_id=release_id,
            environment=environment,
            deployed_by=deployed_by,
            deployed_at=datetime.now(timezone.utc),
            status=status,
            notes=notes,
        )
        deployment_record_repo.add(db, record)

        # If deployment is successful, auto-update linked release plan
        if release_id is not None and status == "success":
            release = await release_plan_repo.get_by_id(db, release_id)
            if release is not None:
                release.status = ReleaseStatus.DEPLOYED
                release.actual_date = datetime.now(timezone.utc).date()

        await db.flush()
        return record


tech_service = TechDevelopmentService()
