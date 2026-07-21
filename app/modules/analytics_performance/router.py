from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.modules.analytics_performance.domain.logic import (
    calculate_indicator_status,
    consolidate_process_kpis,
    generate_trend,
    get_dashboard_kpis,
)
from app.modules.analytics_performance.domain.models import (
    KpiReport,
    PerformanceDashboard,
    PerformanceDataRecord,
    PerformanceIndicator,
    TrendAnalysisReport,
)
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
    KpiGroupedByProcess,
    KpiReportCreate,
    KpiReportResponse,
    TrendAnalysisCreate,
    TrendAnalysisResponse,
    TrendResult,
)

router = APIRouter()


# ─── Performance Indicators ──────────────────────────────────────────────

@router.get("/indicators", response_model=List[IndicatorResponse])
async def list_indicators(
    process_code: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PerformanceIndicator)
    if process_code:
        stmt = stmt.where(PerformanceIndicator.process_code == process_code)
    if is_active is not None:
        stmt = stmt.where(PerformanceIndicator.is_active == is_active)
    result = await db.execute(stmt.order_by(PerformanceIndicator.code))
    return list(result.scalars().all())


@router.post("/indicators", response_model=IndicatorResponse, status_code=status.HTTP_201_CREATED)
async def create_indicator(payload: IndicatorCreate, db: AsyncSession = Depends(get_db)):
    indicator = PerformanceIndicator(**payload.model_dump())
    db.add(indicator)
    await db.flush()
    return indicator


@router.get("/indicators/{indicator_id}", response_model=IndicatorResponse)
async def get_indicator(indicator_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PerformanceIndicator).where(PerformanceIndicator.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator


@router.patch("/indicators/{indicator_id}", response_model=IndicatorResponse)
async def update_indicator(
    indicator_id: int,
    payload: IndicatorUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PerformanceIndicator).where(PerformanceIndicator.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(indicator, field, value)
    await db.flush()
    return indicator


@router.delete("/indicators/{indicator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_indicator(indicator_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PerformanceIndicator).where(PerformanceIndicator.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    await db.delete(indicator)
    await db.flush()


# ─── Performance Data Records ────────────────────────────────────────────

@router.get("/indicators/{indicator_id}/records", response_model=List[DataRecordResponse])
async def list_data_records(
    indicator_id: int,
    period: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(PerformanceDataRecord)
        .where(PerformanceDataRecord.indicator_id == indicator_id)
    )
    if period:
        stmt = stmt.where(PerformanceDataRecord.period == period)
    result = await db.execute(stmt.order_by(PerformanceDataRecord.recorded_at.desc()))
    return list(result.scalars().all())


@router.post(
    "/indicators/{indicator_id}/record",
    response_model=DataRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_data_record(
    indicator_id: int,
    payload: DataRecordCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify indicator exists
    ind_result = await db.execute(
        select(PerformanceIndicator).where(PerformanceIndicator.id == indicator_id)
    )
    indicator = ind_result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")

    record = PerformanceDataRecord(
        indicator_id=indicator_id,
        **payload.model_dump(),
    )
    db.add(record)

    # Calculate status and emit event
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


# ─── Trend Analysis ──────────────────────────────────────────────────────

@router.get("/indicators/{indicator_id}/trend", response_model=TrendResult)
async def get_trend_analysis(
    indicator_id: int,
    from_period: str | None = Query(None, alias="from"),
    to_period: str | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
):
    # Verify indicator exists
    ind_result = await db.execute(
        select(PerformanceIndicator).where(PerformanceIndicator.id == indicator_id)
    )
    if not ind_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Indicator not found")

    stmt = (
        select(PerformanceDataRecord)
        .where(PerformanceDataRecord.indicator_id == indicator_id)
    )
    if from_period:
        stmt = stmt.where(PerformanceDataRecord.period >= from_period)
    if to_period:
        stmt = stmt.where(PerformanceDataRecord.period <= to_period)
    stmt = stmt.order_by(PerformanceDataRecord.period.asc())

    result = await db.execute(stmt)
    records = list(result.scalars().all())

    data_points = [
        {"period": r.period, "value": r.value}
        for r in records
    ]

    return generate_trend(indicator_id, data_points)


# ─── Trend Analysis Reports ──────────────────────────────────────────────

@router.get("/trend-reports", response_model=List[TrendAnalysisResponse])
async def list_trend_reports(
    indicator_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(TrendAnalysisReport)
    if indicator_id:
        stmt = stmt.where(TrendAnalysisReport.indicator_id == indicator_id)
    result = await db.execute(stmt.order_by(TrendAnalysisReport.created_at.desc()))
    return list(result.scalars().all())


@router.post(
    "/trend-reports",
    response_model=TrendAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_trend_report(payload: TrendAnalysisCreate, db: AsyncSession = Depends(get_db)):
    report = TrendAnalysisReport(**payload.model_dump())
    db.add(report)
    await db.flush()
    return report


@router.get("/trend-reports/{report_id}", response_model=TrendAnalysisResponse)
async def get_trend_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrendAnalysisReport).where(TrendAnalysisReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Trend analysis report not found")
    return report


# ─── KPI Reports ─────────────────────────────────────────────────────────

@router.get("/kpi-reports", response_model=List[KpiReportResponse])
async def list_kpi_reports(
    period_start: date | None = None,
    period_end: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(KpiReport)
    if period_start:
        stmt = stmt.where(KpiReport.period_start >= period_start)
    if period_end:
        stmt = stmt.where(KpiReport.period_end <= period_end)
    result = await db.execute(stmt.order_by(KpiReport.created_at.desc()))
    return list(result.scalars().all())


@router.post(
    "/kpi-reports",
    response_model=KpiReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_kpi_report(payload: KpiReportCreate, db: AsyncSession = Depends(get_db)):
    report = KpiReport(**payload.model_dump())
    db.add(report)
    await db.flush()
    return report


@router.get("/kpi-reports/{report_id}", response_model=KpiReportResponse)
async def get_kpi_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KpiReport).where(KpiReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="KPI report not found")
    return report


@router.get("/kpi-reports/consolidated", response_model=List[ConsolidatedReportResponse])
async def get_consolidated_report(
    period: str | None = Query(None, description="Filter by period YYYY-MM"),
    db: AsyncSession = Depends(get_db),
):
    """Consolidated KPI view across all processes for a given period."""
    # Get all distinct process codes from active indicators
    processes_result = await db.execute(
        select(PerformanceIndicator.process_code)
        .where(PerformanceIndicator.is_active.is_(True))
        .distinct()
        .order_by(PerformanceIndicator.process_code)
    )
    process_codes = [row[0] for row in processes_result.all()]

    consolidated: list[ConsolidatedReportResponse] = []
    for code in process_codes:
        kpis = await consolidate_process_kpis(db, code, period)
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
):
    stmt = select(PerformanceDashboard)
    if is_default is not None:
        stmt = stmt.where(PerformanceDashboard.is_default == is_default)
    result = await db.execute(stmt.order_by(PerformanceDashboard.code))
    return list(result.scalars().all())


@router.post(
    "/dashboards",
    response_model=DashboardResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dashboard(payload: DashboardCreate, db: AsyncSession = Depends(get_db)):
    dashboard = PerformanceDashboard(**payload.model_dump())
    db.add(dashboard)
    await db.flush()
    return dashboard


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(dashboard_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PerformanceDashboard).where(PerformanceDashboard.id == dashboard_id)
    )
    dashboard = result.scalar_one_or_none()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.patch("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    payload: DashboardUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PerformanceDashboard).where(PerformanceDashboard.id == dashboard_id)
    )
    dashboard = result.scalar_one_or_none()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dashboard, field, value)
    await db.flush()
    return dashboard


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(dashboard_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PerformanceDashboard).where(PerformanceDashboard.id == dashboard_id)
    )
    dashboard = result.scalar_one_or_none()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    await db.delete(dashboard)
    await db.flush()


@router.get("/dashboards/executive", response_model=ExecutiveDashboardResponse)
async def get_executive_dashboard(db: AsyncSession = Depends(get_db)):
    """Consolidated view with all active KPIs grouped by process and default dashboards."""
    # Fetch dashboards
    dashboards_result = await db.execute(
        select(PerformanceDashboard).order_by(PerformanceDashboard.code)
    )
    dashboards = list(dashboards_result.scalars().all())

    # Fetch all active indicators grouped by process
    indicators_result = await db.execute(
        select(PerformanceIndicator)
        .where(PerformanceIndicator.is_active.is_(True))
        .order_by(PerformanceIndicator.process_code, PerformanceIndicator.code)
    )
    indicators = list(indicators_result.scalars().all())

    # Group by process_code
    grouped: dict[str, list] = {}
    for ind in indicators:
        grouped.setdefault(ind.process_code, []).append(ind)

    kpis_by_process = [
        KpiGroupedByProcess(process_code=code, indicators=inds)
        for code, inds in sorted(grouped.items())
    ]

    return ExecutiveDashboardResponse(dashboards=dashboards, kpis_by_process=kpis_by_process)
