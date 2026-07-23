"""Web routes for Analytics & Performance — Performance Indicators, KPI Reports, Dashboards."""

from __future__ import annotations

import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import PaginationParams
from app.modules.analytics_performance.application.services import analytics_service
from app.web.deps import get_current_user_from_session
from app.web.utils import render
from app.modules.analytics_performance.schemas.dto import (
    IndicatorCreate, IndicatorUpdate,
    DashboardCreate, DashboardUpdate,
    KpiReportCreate,
)

router = APIRouter(prefix="/analytics", tags=["Web — Analytics & Performance"])

_PER_PAGE = 20

# ─── Helpers ──────────────────────────────────────────────────────────────

_PROCESS_NAMES = {
    "P1": "Strategic Planning",
    "P2": "Quality Management",
    "P3": "Commercial Sales",
    "P4": "Tech Development",
    "P5": "PMO Projects",
    "P6": "Training Services",
    "P7": "Human Resources",
    "P8": "Infrastructure/IT",
    "P9": "Procurement",
    "P10": "Customer Experience",
    "P11": "Analytics/Performance",
}

def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


# ─── Root ─────────────────────────────────────────────────────────────────

@router.get("")
async def analytics_root():
    """Sidebar links to /analytics — redirect to executive dashboard."""
    return _redirect("/analytics/dashboards/executive")


# ─── Executive Dashboard ──────────────────────────────────────────────────

@router.get("/dashboards/executive")
async def executive_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    data = await analytics_service.get_executive_dashboard(db)
    # data has 'dashboards' and 'kpis_by_process'
    return render(
        request,
        "pages/analytics/executive_dashboard.html",
        {
            "data": data,
            "process_names": _PROCESS_NAMES,
            "page_title": "Executive Dashboard",
        },
    )


# ─── Performance Indicators ──────────────────────────────────────────────

@router.get("/indicators")
async def list_indicators_view(
    request: Request,
    page: int = 1,
    search: str = "",
    process_code: str = "",
    is_active: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    is_active_bool = None
    if is_active == "true": is_active_bool = True
    elif is_active == "false": is_active_bool = False
    
    # We use a large page size for the web view or proper search
    page_params = PaginationParams(page=page, size=_PER_PAGE)
    items = await analytics_service.list_indicators(db, page_params, process_code, is_active_bool)
    
    # Very simplified total count for web UI since we removed raw SQLAlchemy from here
    total = len(items) if len(items) < _PER_PAGE else page * _PER_PAGE + 1
    total_pages = max(1, page + (1 if len(items) == _PER_PAGE else 0))

    return render(
        request,
        "pages/analytics/indicators.html",
        {
            "items": items,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "search": search,
            "process_code": process_code,
            "is_active": is_active,
            "process_names": _PROCESS_NAMES,
            "page_title": "Performance Indicators",
        },
    )

@router.get("/indicators/create")
async def create_indicator_form(request: Request, user=Depends(get_current_user_from_session)):
    return render(
        request,
        "pages/analytics/indicator_create.html",
        {
            "process_names": _PROCESS_NAMES,
            "page_title": "Create Indicator",
        },
    )

@router.get("/indicators/{indicator_id}")
async def detail_indicator(
    request: Request,
    indicator_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = await analytics_service.get_indicator(db, indicator_id)
    if not item: return _redirect("/analytics/indicators")
    return render(request, "pages/analytics/indicator_detail.html", {"item": item, "process_names": _PROCESS_NAMES, "page_title": f"Indicator — {item.code}"})

@router.get("/indicators/{indicator_id}/edit")
async def edit_indicator_form(
    request: Request,
    indicator_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = await analytics_service.get_indicator(db, indicator_id)
    if not item: return _redirect("/analytics/indicators")
    return render(request, "pages/analytics/indicator_edit.html", {"item": item, "process_names": _PROCESS_NAMES, "page_title": f"Edit — {item.code}"})

@router.post("/indicators")
async def create_indicator(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    process_code: str = Form(...),
    formula: str = Form(""),
    target_value: Optional[float] = Form(None),
    unit: str = Form(""),
    frequency: str = Form("monthly"),
    owner: str = Form(""),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    payload = IndicatorCreate(
        code=code, name=name, description=description or None, process_code=process_code,
        formula=formula or None, target_value=target_value, unit=unit or None,
        frequency=frequency, owner=owner or None, is_active=is_active
    )
    await analytics_service.create_indicator(db, payload)
    await db.commit()
    return _redirect("/analytics/indicators")

@router.post("/indicators/{indicator_id}/edit")
async def edit_indicator(
    request: Request,
    indicator_id: int,
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    process_code: str = Form(...),
    formula: str = Form(""),
    target_value: Optional[float] = Form(None),
    unit: str = Form(""),
    frequency: str = Form("monthly"),
    owner: str = Form(""),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    payload = IndicatorUpdate(
        code=code, name=name, description=description or None, process_code=process_code,
        formula=formula or None, target_value=target_value, unit=unit or None,
        frequency=frequency, owner=owner or None, is_active=is_active
    )
    await analytics_service.update_indicator(db, indicator_id, payload)
    await db.commit()
    return _redirect(f"/analytics/indicators/{indicator_id}")

@router.post("/indicators/{indicator_id}/delete")
async def delete_indicator(
    request: Request,
    indicator_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    await analytics_service.delete_indicator(db, indicator_id)
    await db.commit()
    return _redirect("/analytics/indicators")


# ─── KPI Reports ─────────────────────────────────────────────────────────

@router.get("/kpi-reports")
async def list_kpi_reports(
    request: Request,
    page: int = 1,
    period_start: str = "",
    period_end: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    ps = date.fromisoformat(period_start) if period_start else None
    pe = date.fromisoformat(period_end) if period_end else None
    
    page_params = PaginationParams(page=page, size=_PER_PAGE)
    items = await analytics_service.list_kpi_reports(db, page_params, ps, pe)
    
    total = len(items) if len(items) < _PER_PAGE else page * _PER_PAGE + 1
    total_pages = max(1, page + (1 if len(items) == _PER_PAGE else 0))

    return render(
        request,
        "pages/analytics/kpi_reports.html",
        {
            "items": items,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "period_start": period_start,
            "period_end": period_end,
            "page_title": "KPI Reports",
        },
    )

@router.get("/kpi-reports/create")
async def create_kpi_report_form(request: Request, user=Depends(get_current_user_from_session)):
    return render(request, "pages/analytics/kpi_report_create.html", {"page_title": "Create KPI Report"})

@router.get("/kpi-reports/{report_id}")
async def detail_kpi_report(
    request: Request,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = await analytics_service.get_kpi_report(db, report_id)
    if not item: return _redirect("/analytics/kpi-reports")
    return render(request, "pages/analytics/kpi_report_detail.html", {"item": item, "page_title": f"Report — {item.code}"})

@router.post("/kpi-reports")
async def create_kpi_report(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    period_start: date = Form(...),
    period_end: date = Form(...),
    indicators_data: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    parsed = json.loads(indicators_data) if indicators_data.strip() else None
    payload = KpiReportCreate(code=code, title=title, period_start=period_start, period_end=period_end, indicators_data=parsed)
    await analytics_service.create_kpi_report(db, payload)
    await db.commit()
    return _redirect("/analytics/kpi-reports")

@router.post("/kpi-reports/{report_id}/delete")
async def delete_kpi_report(
    request: Request,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    await analytics_service.delete_kpi_report(db, report_id)
    await db.commit()
    return _redirect("/analytics/kpi-reports")


# ─── Dashboards ──────────────────────────────────────────────────────────

@router.get("/dashboards")
async def list_dashboards(
    request: Request,
    page: int = 1,
    is_default: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    is_default_bool = None
    if is_default == "true": is_default_bool = True
    elif is_default == "false": is_default_bool = False
    
    page_params = PaginationParams(page=page, size=_PER_PAGE)
    items = await analytics_service.list_dashboards(db, page_params, is_default_bool)
    
    total = len(items) if len(items) < _PER_PAGE else page * _PER_PAGE + 1
    total_pages = max(1, page + (1 if len(items) == _PER_PAGE else 0))

    return render(
        request,
        "pages/analytics/dashboards.html",
        {
            "items": items,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "is_default": is_default,
            "page_title": "Dashboards",
        },
    )

@router.get("/dashboards/create")
async def create_dashboard_form(request: Request, user=Depends(get_current_user_from_session)):
    return render(request, "pages/analytics/dashboard_create.html", {"page_title": "Create Dashboard"})

@router.get("/dashboards/{dashboard_id}")
async def detail_dashboard(
    request: Request,
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = await analytics_service.get_dashboard(db, dashboard_id)
    if not item: return _redirect("/analytics/dashboards")
    return render(request, "pages/analytics/dashboard_detail.html", {"item": item, "page_title": f"Dashboard — {item.code}"})

@router.post("/dashboards")
async def create_dashboard(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    is_default: bool = Form(False),
    layout: str = Form(""),
    filters: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    parsed_layout = json.loads(layout) if layout.strip() else None
    parsed_filters = json.loads(filters) if filters.strip() else None
    payload = DashboardCreate(code=code, title=title, is_default=is_default, layout=parsed_layout, filters=parsed_filters)
    await analytics_service.create_dashboard(db, payload)
    await db.commit()
    return _redirect("/analytics/dashboards")

@router.post("/dashboards/{dashboard_id}/delete")
async def delete_dashboard(
    request: Request,
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    await analytics_service.delete_dashboard(db, dashboard_id)
    await db.commit()
    return _redirect("/analytics/dashboards")
