from __future__ import annotations

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.pagination import PaginationParams
from app.modules.analytics_performance.application.services import analytics_service
from app.modules.analytics_performance.schemas.dto import (
    ConsolidatedKpiEntry,
    ConsolidatedReportResponse,
    DashboardCreate,
    DashboardResponse,
    DashboardUpdate,
    DataRecordCreate,
    DataRecordResponse,
    ExecutiveDashboardResponse,
    IndicatorCreate,
    IndicatorResponse,
    IndicatorUpdate,
    KpiReportCreate,
    KpiReportResponse,
    TrendAnalysisCreate,
    TrendAnalysisResponse,
    TrendResult,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# ─── Performance Indicators ──────────────────────────────────────────────

@router.get("/indicators", response_model=List[IndicatorResponse])
async def list_indicators(
    process_code: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await analytics_service.list_indicators(db, page, process_code, is_active)


@router.post(
    "/indicators",
    response_model=IndicatorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))]
)
async def create_indicator(payload: IndicatorCreate, db: AsyncSession = Depends(get_db)):
    return await analytics_service.create_indicator(db, payload)


@router.get("/indicators/{indicator_id}", response_model=IndicatorResponse)
async def get_indicator(indicator_id: int, db: AsyncSession = Depends(get_db)):
    indicator = await analytics_service.get_indicator(db, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator


@router.patch(
    "/indicators/{indicator_id}",
    response_model=IndicatorResponse,
    dependencies=[Depends(RoleChecker("admin", "manager"))]
)
async def update_indicator(indicator_id: int, payload: IndicatorUpdate, db: AsyncSession = Depends(get_db)):
    indicator = await analytics_service.update_indicator(db, indicator_id, payload)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator


@router.delete("/indicators/{indicator_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_indicator(indicator_id: int, db: AsyncSession = Depends(get_db)):
    success = await analytics_service.delete_indicator(db, indicator_id)
    if not success:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return {"message": "Indicator deleted successfully", "id": indicator_id}


@router.patch("/indicators/{indicator_id}/restore", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def restore_indicator(indicator_id: int, db: AsyncSession = Depends(get_db)):
    indicator = await analytics_service.restore_indicator(db, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found or not deleted")
    return indicator


# ─── Performance Data Records ────────────────────────────────────────────

@router.get("/indicators/{indicator_id}/records", response_model=List[DataRecordResponse])
async def list_data_records(
    indicator_id: int,
    period: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await analytics_service.list_data_records(db, page, indicator_id, period)


@router.post(
    "/indicators/{indicator_id}/record",
    response_model=DataRecordResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def submit_data_record(indicator_id: int, payload: DataRecordCreate, db: AsyncSession = Depends(get_db)):
    record = await analytics_service.submit_data_record(db, indicator_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return record


# ─── Trend Analysis ──────────────────────────────────────────────────────

@router.get("/indicators/{indicator_id}/trend", response_model=TrendResult)
async def get_trend_analysis(
    indicator_id: int,
    from_period: str | None = Query(None, alias="from"),
    to_period: str | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
):
    trend = await analytics_service.get_trend_analysis(db, indicator_id, from_period, to_period)
    if not trend:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return trend


# ─── Trend Analysis Reports ──────────────────────────────────────────────

@router.get("/trend-reports", response_model=List[TrendAnalysisResponse])
async def list_trend_reports(
    indicator_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await analytics_service.list_trend_reports(db, page, indicator_id)


@router.post(
    "/trend-reports",
    response_model=TrendAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_trend_report(payload: TrendAnalysisCreate, db: AsyncSession = Depends(get_db)):
    return await analytics_service.create_trend_report(db, payload)


@router.get("/trend-reports/{report_id}", response_model=TrendAnalysisResponse)
async def get_trend_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await analytics_service.get_trend_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Trend analysis report not found")
    return report


@router.delete("/trend-reports/{report_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_trend_report(report_id: int, db: AsyncSession = Depends(get_db)):
    success = await analytics_service.delete_trend_report(db, report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Trend analysis report not found")
    return {"message": "Trend analysis report deleted successfully", "id": report_id}


@router.patch("/trend-reports/{report_id}/restore", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def restore_trend_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await analytics_service.restore_trend_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Trend analysis report not found or not deleted")
    return report


# ─── KPI Reports ─────────────────────────────────────────────────────────

@router.get("/kpi-reports", response_model=List[KpiReportResponse])
async def list_kpi_reports(
    period_start: date | None = None,
    period_end: date | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await analytics_service.list_kpi_reports(db, page, period_start, period_end)


@router.post(
    "/kpi-reports",
    response_model=KpiReportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_kpi_report(payload: KpiReportCreate, db: AsyncSession = Depends(get_db)):
    return await analytics_service.create_kpi_report(db, payload)


@router.get("/kpi-reports/{report_id}", response_model=KpiReportResponse)
async def get_kpi_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await analytics_service.get_kpi_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="KPI report not found")
    return report


@router.delete("/kpi-reports/{report_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_kpi_report(report_id: int, db: AsyncSession = Depends(get_db)):
    success = await analytics_service.delete_kpi_report(db, report_id)
    if not success:
        raise HTTPException(status_code=404, detail="KPI report not found")
    return {"message": "KPI report deleted successfully", "id": report_id}


@router.patch("/kpi-reports/{report_id}/restore", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def restore_kpi_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await analytics_service.restore_kpi_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="KPI report not found or not deleted")
    return report


@router.get("/kpi-reports/consolidated", response_model=List[ConsolidatedReportResponse])
async def get_consolidated_report(
    period: str | None = Query(None, description="Filter by period YYYY-MM"),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.analytics_performance.domain.models import PerformanceIndicator
    from sqlalchemy import select
    # Needed specifically for distinct process_codes
    processes_result = await db.execute(
        select(PerformanceIndicator.process_code)
        .where(PerformanceIndicator.is_active.is_(True), PerformanceIndicator.is_deleted == False)
        .distinct()
        .order_by(PerformanceIndicator.process_code)
    )
    process_codes = [row[0] for row in processes_result.all()]

    consolidated = []
    for code in process_codes:
        kpis = await analytics_service.consolidate_process_kpis(db, code, period)
        consolidated.append(
            ConsolidatedReportResponse(
                process_code=code,
                period=period,
                indicators=[ConsolidatedKpiEntry(**kpi) for kpi in kpis],
            )
        )

    return consolidated


# ─── Performance Dashboards ──────────────────────────────────────────────

@router.get("/dashboards", response_model=List[DashboardResponse])
async def list_dashboards(
    is_default: bool | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await analytics_service.list_dashboards(db, page, is_default)


@router.post(
    "/dashboards",
    response_model=DashboardResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_dashboard(payload: DashboardCreate, db: AsyncSession = Depends(get_db)):
    return await analytics_service.create_dashboard(db, payload)


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(dashboard_id: int, db: AsyncSession = Depends(get_db)):
    dashboard = await analytics_service.get_dashboard(db, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.patch(
    "/dashboards/{dashboard_id}",
    response_model=DashboardResponse,
    dependencies=[Depends(RoleChecker("admin", "manager"))]
)
async def update_dashboard(dashboard_id: int, payload: DashboardUpdate, db: AsyncSession = Depends(get_db)):
    dashboard = await analytics_service.update_dashboard(db, dashboard_id, payload)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.delete("/dashboards/{dashboard_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_dashboard(dashboard_id: int, db: AsyncSession = Depends(get_db)):
    success = await analytics_service.delete_dashboard(db, dashboard_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"message": "Dashboard deleted successfully", "id": dashboard_id}


@router.patch("/dashboards/{dashboard_id}/restore", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def restore_dashboard(dashboard_id: int, db: AsyncSession = Depends(get_db)):
    dashboard = await analytics_service.restore_dashboard(db, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or not deleted")
    return dashboard


@router.get("/dashboards/executive", response_model=ExecutiveDashboardResponse)
async def get_executive_dashboard(db: AsyncSession = Depends(get_db)):
    data = await analytics_service.get_executive_dashboard(db)
    return ExecutiveDashboardResponse(**data)
