from typing import Optional, TypeVar, Generic, Type
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics_performance.domain.models import (
    KpiReport,
    PerformanceDashboard,
    PerformanceDataRecord,
    PerformanceIndicator,
    TrendAnalysisReport,
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
            obj.is_deleted = True
            obj.deleted_at = datetime.now(timezone.utc)
        else:
            await db.delete(obj)


class PerformanceIndicatorRepository(BaseRepository[PerformanceIndicator]):
    def __init__(self):
        super().__init__(PerformanceIndicator)

    async def get_all_indicators(
        self,
        db: AsyncSession,
        process_code: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[PerformanceIndicator]:
        stmt = select(PerformanceIndicator).where(PerformanceIndicator.is_deleted == False)
        if process_code:
            stmt = stmt.where(PerformanceIndicator.process_code == process_code)
        if is_active is not None:
            stmt = stmt.where(PerformanceIndicator.is_active == is_active)
        stmt = stmt.order_by(PerformanceIndicator.code)
        result = await db.execute(stmt)
        return list(result.scalars().all())


class PerformanceDataRecordRepository(BaseRepository[PerformanceDataRecord]):
    def __init__(self):
        super().__init__(PerformanceDataRecord)

    async def get_records_by_indicator(
        self,
        db: AsyncSession,
        indicator_id: int,
        period: Optional[str] = None,
    ) -> list[PerformanceDataRecord]:
        stmt = (
            select(PerformanceDataRecord)
            .where(
                PerformanceDataRecord.indicator_id == indicator_id,
                PerformanceDataRecord.is_deleted == False,
            )
        )
        if period:
            stmt = stmt.where(PerformanceDataRecord.period == period)
        stmt = stmt.order_by(PerformanceDataRecord.recorded_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_indicator(
        self, db: AsyncSession, indicator_id: int
    ) -> Optional[PerformanceDataRecord]:
        stmt = (
            select(PerformanceDataRecord)
            .where(PerformanceDataRecord.indicator_id == indicator_id)
            .order_by(PerformanceDataRecord.recorded_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


class KpiReportRepository(BaseRepository[KpiReport]):
    def __init__(self):
        super().__init__(KpiReport)

    async def get_reports_by_period(
        self,
        db: AsyncSession,
        period_start=None,
        period_end=None,
    ) -> list[KpiReport]:
        stmt = select(KpiReport).where(KpiReport.is_deleted == False)
        if period_start:
            stmt = stmt.where(KpiReport.period_start >= period_start)
        if period_end:
            stmt = stmt.where(KpiReport.period_end <= period_end)
        stmt = stmt.order_by(KpiReport.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())


class PerformanceDashboardRepository(BaseRepository[PerformanceDashboard]):
    def __init__(self):
        super().__init__(PerformanceDashboard)

    async def get_default_dashboard(self, db: AsyncSession) -> Optional[PerformanceDashboard]:
        stmt = select(PerformanceDashboard).where(
            PerformanceDashboard.is_default == True,
            PerformanceDashboard.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_dashboards(
        self, db: AsyncSession, is_default: Optional[bool] = None
    ) -> list[PerformanceDashboard]:
        stmt = select(PerformanceDashboard).where(PerformanceDashboard.is_deleted == False)
        if is_default is not None:
            stmt = stmt.where(PerformanceDashboard.is_default == is_default)
        stmt = stmt.order_by(PerformanceDashboard.code)
        result = await db.execute(stmt)
        return list(result.scalars().all())


class TrendAnalysisReportRepository(BaseRepository[TrendAnalysisReport]):
    def __init__(self):
        super().__init__(TrendAnalysisReport)

    async def get_reports_by_indicator(
        self, db: AsyncSession, indicator_id: int
    ) -> list[TrendAnalysisReport]:
        stmt = select(TrendAnalysisReport).where(
            TrendAnalysisReport.indicator_id == indicator_id,
            TrendAnalysisReport.is_deleted == False,
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


# Singletons
indicator_repo = PerformanceIndicatorRepository()
data_record_repo = PerformanceDataRecordRepository()
kpi_report_repo = KpiReportRepository()
dashboard_repo = PerformanceDashboardRepository()
trend_report_repo = TrendAnalysisReportRepository()
