from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── PerformanceIndicator ────────────────────────────────────────────────

class IndicatorCreate(BaseModel):
    code: str = Field(..., pattern=r"^KPI-P(1[0-1]|[1-9])-\d{3}$")
    name: str
    description: Optional[str] = None
    process_code: str = Field(..., pattern=r"P(1[0-1]|[1-9])")
    formula: Optional[str] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None
    frequency: str = "monthly"
    owner: Optional[str] = None


class IndicatorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    formula: Optional[str] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None
    frequency: Optional[str] = None
    owner: Optional[str] = None
    is_active: Optional[bool] = None


class IndicatorResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    process_code: str
    formula: Optional[str]
    target_value: Optional[float]
    unit: Optional[str]
    frequency: str
    owner: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── PerformanceDataRecord ───────────────────────────────────────────────

class DataRecordCreate(BaseModel):
    period: str = Field(..., pattern=r"^\d{4}(-\d{2})?$")
    value: float
    recorded_by: str
    notes: Optional[str] = None


class DataRecordResponse(BaseModel):
    id: int
    indicator_id: int
    period: str
    value: float
    recorded_at: datetime
    recorded_by: str
    notes: Optional[str]

    model_config = {"from_attributes": True}


# ─── KpiReport ──────────────────────────────────────────────────────────

class KpiReportCreate(BaseModel):
    code: str
    title: str
    period_start: date
    period_end: date
    indicators_data: Optional[List[Dict[str, Any]]] = None


class KpiReportResponse(BaseModel):
    id: int
    code: str
    title: str
    period_start: date
    period_end: date
    indicators_data: Optional[list]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── PerformanceDashboard ───────────────────────────────────────────────

class DashboardCreate(BaseModel):
    code: str
    title: str
    layout: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    is_default: bool = False


class DashboardUpdate(BaseModel):
    title: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


class DashboardResponse(BaseModel):
    id: int
    code: str
    title: str
    layout: Optional[dict]
    filters: Optional[dict]
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── TrendAnalysisReport ────────────────────────────────────────────────

class TrendAnalysisCreate(BaseModel):
    code: str
    indicator_id: int
    period_start: date
    period_end: date
    trend: str  # up, down, flat, volatile
    change_percent: Optional[float] = None
    insights: Optional[str] = None
    recommendations: Optional[str] = None


class TrendAnalysisResponse(BaseModel):
    id: int
    code: str
    indicator_id: int
    period_start: date
    period_end: date
    trend: str
    change_percent: Optional[float]
    insights: Optional[str]
    recommendations: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Composite / Views ──────────────────────────────────────────────────

class KpiGroupedByProcess(BaseModel):
    process_code: str
    indicators: List[IndicatorResponse]


class ExecutiveDashboardResponse(BaseModel):
    dashboards: List[DashboardResponse]
    kpis_by_process: List[KpiGroupedByProcess]


class ConsolidatedKpiEntry(BaseModel):
    indicator_id: int
    code: str
    name: str
    formula: Optional[str]
    target: Optional[float]
    unit: Optional[str]
    latest_value: Optional[float]
    latest_period: Optional[str]
    status: str


class ConsolidatedReportResponse(BaseModel):
    process_code: str
    period: Optional[str]
    indicators: List[ConsolidatedKpiEntry]


class TrendResult(BaseModel):
    indicator_id: int
    direction: str
    slope: float
    volatility: float
    change_percent: float
