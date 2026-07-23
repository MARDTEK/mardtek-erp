from typing import Optional, TypeVar, Generic, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tech_development.domain.models import (
    DeploymentRecord,
    ProductRoadmap,
    QATestReport,
    ReleasePlan,
    RiskMatrix,
    SolutionSunset,
    TechnicalSpecification,
    UATSignOff,
)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[T]:
        result = await db.execute(select(self.model_class).where(self.model_class.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        filters: Optional[dict] = None,
        order_by=None,
        include_deleted: bool = False,
    ) -> list[T]:
        stmt = select(self.model_class)
        if not include_deleted and hasattr(self.model_class, "is_deleted"):
            stmt = stmt.where(self.model_class.is_deleted == False)
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    stmt = stmt.where(getattr(self.model_class, field_name) == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    def add(self, db: AsyncSession, obj: T) -> None:
        db.add(obj)

    async def delete(self, db: AsyncSession, obj: T) -> None:
        if hasattr(obj, "is_deleted"):
            from datetime import datetime, timezone
            obj.is_deleted = True
            obj.deleted_at = datetime.now(timezone.utc)
        else:
            await db.delete(obj)


class ProductRoadmapRepository(BaseRepository[ProductRoadmap]):
    def __init__(self):
        super().__init__(ProductRoadmap)

    async def get_active_by_product_line(self, db: AsyncSession, product_line: str) -> list[ProductRoadmap]:
        stmt = (
            select(ProductRoadmap)
            .where(
                ProductRoadmap.product_line == product_line,
                ProductRoadmap.status == "published",
                ProductRoadmap.is_deleted == False,
            )
            .order_by(ProductRoadmap.year.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class ReleasePlanRepository(BaseRepository[ReleasePlan]):
    def __init__(self):
        super().__init__(ReleasePlan)

    async def get_by_status(self, db: AsyncSession, status: str) -> list[ReleasePlan]:
        stmt = (
            select(ReleasePlan)
            .where(ReleasePlan.status == status, ReleasePlan.is_deleted == False)
            .order_by(ReleasePlan.planned_date.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class TechnicalSpecificationRepository(BaseRepository[TechnicalSpecification]):
    def __init__(self):
        super().__init__(TechnicalSpecification)


class RiskMatrixRepository(BaseRepository[RiskMatrix]):
    def __init__(self):
        super().__init__(RiskMatrix)


class QATestReportRepository(BaseRepository[QATestReport]):
    def __init__(self):
        super().__init__(QATestReport)


class DeploymentRecordRepository(BaseRepository[DeploymentRecord]):
    def __init__(self):
        super().__init__(DeploymentRecord)


class UATSignOffRepository(BaseRepository[UATSignOff]):
    def __init__(self):
        super().__init__(UATSignOff)


class SolutionSunsetRepository(BaseRepository[SolutionSunset]):
    def __init__(self):
        super().__init__(SolutionSunset)


# Instances
roadmap_repo = ProductRoadmapRepository()
release_plan_repo = ReleasePlanRepository()
tech_spec_repo = TechnicalSpecificationRepository()
risk_matrix_repo = RiskMatrixRepository()
qa_test_report_repo = QATestReportRepository()
deployment_record_repo = DeploymentRecordRepository()
uat_signoff_repo = UATSignOffRepository()
solution_sunset_repo = SolutionSunsetRepository()
