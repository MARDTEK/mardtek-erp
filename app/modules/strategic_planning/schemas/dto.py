from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Quality Policy ──────────────────────────────────────────────────────

class QualityPolicyCreate(BaseModel):
    code: str = Field(..., pattern=r"^POL-P1-\d{3}")
    title: str
    content: str
    version: str = "1.0"


class QualityPolicyUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    version: Optional[str] = None


class QualityPolicyApprove(BaseModel):
    approved_by: str


class QualityPolicyResponse(BaseModel):
    id: int
    code: str
    title: str
    content: str
    version: str
    status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Quality Objective ───────────────────────────────────────────────────

class QualityObjectiveCreate(BaseModel):
    code: str = Field(..., pattern=r"^MAT-P1-\d{3}")
    objective: str
    process_code: str = Field(..., pattern=r"P(1[0-1]|[1-9])")
    target_value: float = Field(..., gt=0)
    metric_unit: str
    year: int = Field(..., ge=2020, le=2100)
    responsible: str


class QualityObjectiveUpdateProgress(BaseModel):
    actual_value: float


class QualityObjectiveResponse(BaseModel):
    id: int
    code: str
    objective: str
    process_code: str
    target_value: float
    actual_value: Optional[float]
    metric_unit: str
    year: int
    status: str
    responsible: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Marketing Plan ──────────────────────────────────────────────────────

class MarketingPlanCreate(BaseModel):
    code: str = Field(..., pattern=r"^PLN-P1-\d{3}")
    title: str
    year: int = Field(..., ge=2020, le=2100)
    goals: str
    budget: Decimal = Field(..., decimal_places=2)
    activities: List[Dict[str, Any]] = []


class MarketingPlanUpdate(BaseModel):
    title: Optional[str] = None
    goals: Optional[str] = None
    budget: Optional[Decimal] = None
    activities: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class MarketingPlanResponse(BaseModel):
    id: int
    code: str
    title: str
    year: int
    goals: str
    budget: Decimal
    activities: list
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Strategy Review ─────────────────────────────────────────────────────

class StrategyReviewCreate(BaseModel):
    date: date
    reviewed_by: str
    summary: str
    decisions: str
    next_review_date: Optional[date] = None


class StrategyReviewResponse(BaseModel):
    id: int
    date: date
    reviewed_by: str
    summary: str
    decisions: str
    next_review_date: Optional[date]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Management Review Report ────────────────────────────────────────────

class ManagementReviewCreate(BaseModel):
    code: str = Field(..., pattern=r"^INF-P1-\d{3}")
    title: str
    review_period_start: date
    review_period_end: date
    prepared_by: str
    summary: str
    conclusions: Dict[str, Any] = {}
    report_url: Optional[str] = None


class ManagementReviewResponse(BaseModel):
    id: int
    code: str
    title: str
    review_period_start: date
    review_period_end: date
    prepared_by: str
    summary: str
    conclusions: dict
    report_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── QMS Scope ───────────────────────────────────────────────────────────

class QmsScopeCreate(BaseModel):
    version: str = "1.0"
    scope_description: str
    exclusions: Optional[str] = None
    applicable_normative: str
    approved_by: Optional[str] = None


class QmsScopeUpdate(BaseModel):
    scope_description: Optional[str] = None
    exclusions: Optional[str] = None
    applicable_normative: Optional[str] = None
    approved_by: Optional[str] = None


class QmsScopeResponse(BaseModel):
    id: int
    version: str
    scope_description: str
    exclusions: Optional[str]
    applicable_normative: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    is_current: bool
    created_at: datetime

    model_config = {"from_attributes": True}
