"""Business logic for P4 — Design & Development of Solutions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tech_development.domain.models import (
    DeploymentEnvironment,
    DeploymentRecord,
    DeploymentStatus,
    ProductRoadmap,
    ProductLine,
    QATestReport,
    ReleasePlan,
    ReleaseStatus,
)


# ─── QA Logic ─────────────────────────────────────────────────────────────


def calculate_qa_pass_rate(report: QATestReport) -> float:
    """Return the pass rate as a float percentage (0–100).

    If the report has zero total tests the rate is 0.0 to avoid division
    by zero.
    """
    if report.total_tests == 0:
        return 0.0
    return round((report.passed / report.total_tests) * 100, 2)


# ─── Release Query Logic ──────────────────────────────────────────────────


async def get_release_by_status(db: AsyncSession, status: str) -> list[ReleasePlan]:
    """Return all release plans filtered by status string value."""
    result = await db.execute(
        select(ReleasePlan)
        .where(ReleasePlan.status == status)
        .order_by(ReleasePlan.planned_date.desc())
    )
    return list(result.scalars().all())


async def get_active_roadmap_items(
    db: AsyncSession, product_line: str
) -> list[ProductRoadmap]:
    """Return published roadmaps for a given product line, newest first."""
    result = await db.execute(
        select(ProductRoadmap)
        .where(
            ProductRoadmap.product_line == product_line,
            ProductRoadmap.status == "published",
        )
        .order_by(ProductRoadmap.year.desc())
    )
    return list(result.scalars().all())


# ─── Deployment Logic ─────────────────────────────────────────────────────


async def create_deployment_record(
    db: AsyncSession,
    code: str,
    environment: str,
    deployed_by: str,
    release_id: int | None = None,
    status: str = "success",
    notes: str | None = None,
) -> DeploymentRecord:
    """Create and persist a deployment record.

    Returns the newly created record (flushed but not committed — the
    caller's session commit handles finalisation).
    """
    record = DeploymentRecord(
        code=code,
        release_id=release_id,
        environment=environment,
        deployed_by=deployed_by,
        deployed_at=datetime.now(timezone.utc),
        status=status,
        notes=notes,
    )
    db.add(record)

    # If deployment is successful, auto-update linked release plan
    if release_id is not None and status == "success":
        result = await db.execute(
            select(ReleasePlan).where(ReleasePlan.id == release_id)
        )
        release = result.scalar_one_or_none()
        if release is not None:
            release.status = ReleaseStatus.DEPLOYED
            release.actual_date = datetime.now(timezone.utc).date()

    await db.flush()
    return record
