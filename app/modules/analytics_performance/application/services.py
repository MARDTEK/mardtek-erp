"""Application services for P11 — Analytics & Performance."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.core.pagination import PaginationParams, paginate
from app.core.event_bus import Event, event_bus
from app.modules.analytics_performance.domain.logic import calculate_indicator_status, generate_trend
from app.modules.analytics_performance.domain.models import (
    PerformanceIndicator,
    PerformanceDataRecord,
    KpiReport,
    PerformanceDashboard,
    TrendAnalysisReport,
)
from app.modules.analytics_performance.infrastructure.repositories import (
    data_record_repo,
    dashboard_repo,
    indicator_repo,
    kpi_report_repo,
    trend_report_repo,
)
from app.modules.analytics_performance.schemas.dto import (
    DashboardCreate,
    DashboardUpdate,
    DataRecordCreate,
    IndicatorCreate,
    IndicatorUpdate,
    KpiReportCreate,
    TrendAnalysisCreate,
    TrendResult,
    KpiGroupedByProcess,
)


class AnalyticsService:
    # ─── Performance Indicators ──────────────────────────────────────────────
    @staticmethod
    async def list_indicators(
        db: AsyncSession,
        page: PaginationParams,
        process_code: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[PerformanceIndicator]:
        stmt = select(PerformanceIndicator).where(PerformanceIndicator.is_deleted == False)
        if process_code:
            stmt = stmt.where(PerformanceIndicator.process_code == process_code)
        if is_active is not None:
            stmt = stmt.where(PerformanceIndicator.is_active == is_active)
        result = await db.execute(paginate(stmt.order_by(PerformanceIndicator.code), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_indicator(db: AsyncSession, payload: IndicatorCreate) -> PerformanceIndicator:
        indicator = PerformanceIndicator(**payload.model_dump())
        indicator_repo.add(db, indicator)
        await db.flush()
        return indicator

    @staticmethod
    async def get_indicator(db: AsyncSession, indicator_id: int) -> Optional[PerformanceIndicator]:
        indicator = await indicator_repo.get_by_id(db, indicator_id)
        if indicator and not indicator.is_deleted:
            return indicator
        return None

    @staticmethod
    async def update_indicator(db: AsyncSession, indicator_id: int, payload: IndicatorUpdate) -> Optional[PerformanceIndicator]:
        indicator = await AnalyticsService.get_indicator(db, indicator_id)
        if not indicator:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(indicator, field, value)
        await db.flush()
        return indicator

    @staticmethod
    async def delete_indicator(db: AsyncSession, indicator_id: int) -> bool:
        indicator = await AnalyticsService.get_indicator(db, indicator_id)
        if not indicator:
            return False
        await indicator_repo.delete(db, indicator)
        await db.flush()
        return True

    @staticmethod
    async def restore_indicator(db: AsyncSession, indicator_id: int) -> Optional[PerformanceIndicator]:
        indicator = await indicator_repo.get_by_id(db, indicator_id)
        if not indicator or not indicator.is_deleted:
            return None
        indicator.is_deleted = False
        indicator.deleted_at = None
        await db.flush()
        return indicator

    # ─── Data Records ────────────────────────────────────────────────────────
    @staticmethod
    async def list_data_records(
        db: AsyncSession,
        page: PaginationParams,
        indicator_id: int,
        period: Optional[str] = None,
    ) -> List[PerformanceDataRecord]:
        stmt = (
            select(PerformanceDataRecord)
            .where(PerformanceDataRecord.indicator_id == indicator_id, PerformanceDataRecord.is_deleted == False)
        )
        if period:
            stmt = stmt.where(PerformanceDataRecord.period == period)
        result = await db.execute(paginate(stmt.order_by(PerformanceDataRecord.recorded_at.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def submit_data_record(
        db: AsyncSession, indicator_id: int, payload: DataRecordCreate
    ) -> Optional[PerformanceDataRecord]:
        indicator = await AnalyticsService.get_indicator(db, indicator_id)
        if not indicator:
            return None

        record = PerformanceDataRecord(indicator_id=indicator_id, **payload.model_dump())
        data_record_repo.add(db, record)

        status_value = calculate_indicator_status(payload.value, indicator.target_value)
        await db.flush()

        await event_bus.emit(
            Event(
                name="KPICalculated",
                payload={
                    "indicator_id": indicator_id,
                    "indicator_code": indicator.code,
                    "period": payload.period,
                    "value": payload.value,
                    "target": indicator.target_value,
                    "status": status_value,
                    "record_id": record.id,
                    "recorded_by": payload.recorded_by,
                },
                source_module="analytics_performance",
            )
        )
        return record

    @staticmethod
    async def get_trend_analysis(db: AsyncSession, indicator_id: int, from_period: Optional[str], to_period: Optional[str]) -> Optional[TrendResult]:
        indicator = await AnalyticsService.get_indicator(db, indicator_id)
        if not indicator:
            return None

        stmt = select(PerformanceDataRecord).where(PerformanceDataRecord.indicator_id == indicator_id, PerformanceDataRecord.is_deleted == False)
        if from_period:
            stmt = stmt.where(PerformanceDataRecord.period >= from_period)
        if to_period:
            stmt = stmt.where(PerformanceDataRecord.period <= to_period)
        stmt = stmt.order_by(PerformanceDataRecord.period.asc())

        result = await db.execute(stmt)
        records = list(result.scalars().all())

        data_points = [{"period": r.period, "value": r.value} for r in records]
        return generate_trend(indicator_id, data_points)

    # ─── Trend Reports ───────────────────────────────────────────────────────
    @staticmethod
    async def list_trend_reports(
        db: AsyncSession,
        page: PaginationParams,
        indicator_id: Optional[int] = None,
    ) -> List[TrendAnalysisReport]:
        stmt = select(TrendAnalysisReport).where(TrendAnalysisReport.is_deleted == False)
        if indicator_id:
            stmt = stmt.where(TrendAnalysisReport.indicator_id == indicator_id)
        result = await db.execute(paginate(stmt.order_by(TrendAnalysisReport.created_at.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_trend_report(db: AsyncSession, payload: TrendAnalysisCreate) -> TrendAnalysisReport:
        report = TrendAnalysisReport(**payload.model_dump())
        trend_report_repo.add(db, report)
        await db.flush()
        return report

    @staticmethod
    async def get_trend_report(db: AsyncSession, report_id: int) -> Optional[TrendAnalysisReport]:
        report = await trend_report_repo.get_by_id(db, report_id)
        if report and not report.is_deleted:
            return report
        return None

    @staticmethod
    async def delete_trend_report(db: AsyncSession, report_id: int) -> bool:
        report = await AnalyticsService.get_trend_report(db, report_id)
        if not report:
            return False
        await trend_report_repo.delete(db, report)
        await db.flush()
        return True
        
    @staticmethod
    async def restore_trend_report(db: AsyncSession, report_id: int) -> Optional[TrendAnalysisReport]:
        report = await trend_report_repo.get_by_id(db, report_id)
        if not report or not report.is_deleted:
            return None
        report.is_deleted = False
        report.deleted_at = None
        await db.flush()
        return report

    # ─── KPI Reports ─────────────────────────────────────────────────────────
    @staticmethod
    async def list_kpi_reports(
        db: AsyncSession,
        page: PaginationParams,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
    ) -> List[KpiReport]:
        stmt = select(KpiReport).where(KpiReport.is_deleted == False)
        if period_start:
            stmt = stmt.where(KpiReport.period_start >= period_start)
        if period_end:
            stmt = stmt.where(KpiReport.period_end <= period_end)
        result = await db.execute(paginate(stmt.order_by(KpiReport.created_at.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_kpi_report(db: AsyncSession, payload: KpiReportCreate) -> KpiReport:
        report = KpiReport(**payload.model_dump())
        kpi_report_repo.add(db, report)
        await db.flush()
        return report

    @staticmethod
    async def get_kpi_report(db: AsyncSession, report_id: int) -> Optional[KpiReport]:
        report = await kpi_report_repo.get_by_id(db, report_id)
        if report and not report.is_deleted:
            return report
        return None

    @staticmethod
    async def delete_kpi_report(db: AsyncSession, report_id: int) -> bool:
        report = await AnalyticsService.get_kpi_report(db, report_id)
        if not report:
            return False
        await kpi_report_repo.delete(db, report)
        await db.flush()
        return True

    @staticmethod
    async def restore_kpi_report(db: AsyncSession, report_id: int) -> Optional[KpiReport]:
        report = await kpi_report_repo.get_by_id(db, report_id)
        if not report or not report.is_deleted:
            return None
        report.is_deleted = False
        report.deleted_at = None
        await db.flush()
        return report

    # ─── Dashboards ──────────────────────────────────────────────────────────
    @staticmethod
    async def list_dashboards(
        db: AsyncSession,
        page: PaginationParams,
        is_default: Optional[bool] = None,
    ) -> List[PerformanceDashboard]:
        stmt = select(PerformanceDashboard).where(PerformanceDashboard.is_deleted == False)
        if is_default is not None:
            stmt = stmt.where(PerformanceDashboard.is_default == is_default)
        result = await db.execute(paginate(stmt.order_by(PerformanceDashboard.code), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_dashboard(db: AsyncSession, payload: DashboardCreate) -> PerformanceDashboard:
        dashboard = PerformanceDashboard(**payload.model_dump())
        dashboard_repo.add(db, dashboard)
        await db.flush()
        return dashboard

    @staticmethod
    async def get_dashboard(db: AsyncSession, dashboard_id: int) -> Optional[PerformanceDashboard]:
        dashboard = await dashboard_repo.get_by_id(db, dashboard_id)
        if dashboard and not dashboard.is_deleted:
            return dashboard
        return None

    @staticmethod
    async def update_dashboard(db: AsyncSession, dashboard_id: int, payload: DashboardUpdate) -> Optional[PerformanceDashboard]:
        dashboard = await AnalyticsService.get_dashboard(db, dashboard_id)
        if not dashboard:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(dashboard, field, value)
        await db.flush()
        return dashboard

    @staticmethod
    async def delete_dashboard(db: AsyncSession, dashboard_id: int) -> bool:
        dashboard = await AnalyticsService.get_dashboard(db, dashboard_id)
        if not dashboard:
            return False
        await dashboard_repo.delete(db, dashboard)
        await db.flush()
        return True

    @staticmethod
    async def restore_dashboard(db: AsyncSession, dashboard_id: int) -> Optional[PerformanceDashboard]:
        dashboard = await dashboard_repo.get_by_id(db, dashboard_id)
        if not dashboard or not dashboard.is_deleted:
            return None
        dashboard.is_deleted = False
        dashboard.deleted_at = None
        await db.flush()
        return dashboard

    # ─── Complex Views ───────────────────────────────────────────────────────
    @staticmethod
    async def get_dashboard_kpis(
        db: AsyncSession,
        dashboard_id: int,
    ) -> list[dict[str, Any]]:
        dashboard = await dashboard_repo.get_by_id(db, dashboard_id)
        if dashboard is None:
            return []

        indicators = await indicator_repo.get_all(db, filters={"is_active": True})
        aggregated: list[dict[str, Any]] = []
        for ind in indicators:
            record = await data_record_repo.get_latest_by_indicator(db, ind.id)
            aggregated.append({
                "indicator_id": ind.id,
                "code": ind.code,
                "name": ind.name,
                "process_code": ind.process_code,
                "target": ind.target_value,
                "unit": ind.unit,
                "latest_value": record.value if record else None,
                "latest_period": record.period if record else None,
                "status": calculate_indicator_status(record.value, ind.target_value) if record else "no_data",
            })
        return aggregated

    @staticmethod
    async def consolidate_process_kpis(
        db: AsyncSession,
        process_code: str,
        period: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        indicators = await indicator_repo.get_all_indicators(
            db, process_code=process_code, is_active=True
        )

        consolidated: list[dict[str, Any]] = []
        for ind in indicators:
            records = await data_record_repo.get_records_by_indicator(db, ind.id, period=period)
            record = records[0] if records else None

            consolidated.append({
                "indicator_id": ind.id,
                "code": ind.code,
                "name": ind.name,
                "formula": ind.formula,
                "target": ind.target_value,
                "unit": ind.unit,
                "latest_value": record.value if record else None,
                "latest_period": record.period if record else None,
                "status": calculate_indicator_status(record.value, ind.target_value) if record else "no_data",
            })
        return consolidated

    @staticmethod
    async def get_executive_dashboard(db: AsyncSession) -> dict[str, Any]:
        dashboards = await dashboard_repo.get_all_dashboards(db)
        
        stmt = (
            select(PerformanceIndicator)
            .where(PerformanceIndicator.is_active.is_(True), PerformanceIndicator.is_deleted == False)
            .order_by(PerformanceIndicator.process_code, PerformanceIndicator.code)
        )
        result = await db.execute(stmt)
        indicators = list(result.scalars().all())

        grouped: dict[str, list] = {}
        for ind in indicators:
            grouped.setdefault(ind.process_code, []).append(ind)

        kpis_by_process = [
            KpiGroupedByProcess(process_code=code, indicators=inds)
            for code, inds in sorted(grouped.items())
        ]

        # For the dashboard, let's also fetch the latest record for each active indicator
        # so we can show their actual status.
        return {"dashboards": dashboards, "kpis_by_process": kpis_by_process}


analytics_service = AnalyticsService()
