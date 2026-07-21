"""P4 — Design & Development of Solutions: Pydantic v2 schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── ProductRoadmap ───────────────────────────────────────────────────────


class ProductRoadmapCreate(BaseModel):
    code: str = Field(..., pattern=r"^PLN-P4-\d{3}")
    title: str
    product_line: str = Field(..., pattern=r"^(SERVICIOS|SAAS)$")
    year: int = Field(..., ge=2020, le=2100)
    vision: str
    strategic_goals: str
    items: List[Dict[str, Any]] = []
    status: str = "draft"


class ProductRoadmapUpdate(BaseModel):
    title: Optional[str] = None
    vision: Optional[str] = None
    strategic_goals: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class ProductRoadmapResponse(BaseModel):
    id: int
    code: str
    title: str
    product_line: str
    year: int
    vision: str
    strategic_goals: str
    items: list
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── ReleasePlan ──────────────────────────────────────────────────────────


class ReleasePlanCreate(BaseModel):
    code: str = Field(..., pattern=r"^PLN-P4-\d{3}")
    title: str
    version: str
    product: str
    planned_date: date
    features: List[Dict[str, Any]] = []
    status: str = "planned"
    release_notes: Optional[str] = None


class ReleasePlanUpdate(BaseModel):
    title: Optional[str] = None
    version: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    features: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    release_notes: Optional[str] = None


class ReleasePlanResponse(BaseModel):
    id: int
    code: str
    title: str
    version: str
    product: str
    planned_date: date
    actual_date: Optional[date]
    features: list
    status: str
    release_notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── TechnicalSpecification ───────────────────────────────────────────────


class TechnicalSpecificationCreate(BaseModel):
    code: str
    title: str
    project_id: Optional[int] = None
    product: Optional[str] = None
    version: str = "1.0"
    content: str
    status: str = "draft"


class TechnicalSpecificationUpdate(BaseModel):
    title: Optional[str] = None
    version: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    approved_by: Optional[str] = None


class TechnicalSpecificationResponse(BaseModel):
    id: int
    code: str
    title: str
    project_id: Optional[int]
    product: Optional[str]
    version: str
    content: str
    status: str
    approved_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── RiskMatrix ───────────────────────────────────────────────────────────


class RiskMatrixCreate(BaseModel):
    code: str = Field(..., pattern=r"^MAT-P4-\d{3}")
    project_id: Optional[int] = None
    risks: List[Dict[str, Any]] = []
    version: str = "1.0"


class RiskMatrixUpdate(BaseModel):
    risks: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None


class RiskMatrixResponse(BaseModel):
    id: int
    code: str
    project_id: Optional[int]
    risks: list
    version: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── QATestReport ─────────────────────────────────────────────────────────


class QATestReportCreate(BaseModel):
    code: str = Field(..., pattern=r"^INF-P4-\d{3}")
    title: str
    release_id: Optional[int] = None
    test_type: str = Field(..., pattern=r"^(unit|integration|e2e|regression)$")
    total_tests: int = Field(..., ge=0)
    passed: int = Field(..., ge=0)
    failed: int = Field(..., ge=0)
    blocked: int = 0
    report_url: Optional[str] = None
    status: str = "draft"


class QATestReportUpdate(BaseModel):
    title: Optional[str] = None
    total_tests: Optional[int] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    blocked: Optional[int] = None
    report_url: Optional[str] = None
    status: Optional[str] = None


class QATestReportResponse(BaseModel):
    id: int
    code: str
    title: str
    release_id: Optional[int]
    test_type: str
    total_tests: int
    passed: int
    failed: int
    blocked: int
    report_url: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── DeploymentRecord ─────────────────────────────────────────────────────


class DeploymentRecordCreate(BaseModel):
    code: str = Field(..., pattern=r"^REG-P4-\d{3}")
    release_id: Optional[int] = None
    environment: str = Field(..., pattern=r"^(dev|staging|production)$")
    deployed_by: str
    status: str = "success"
    notes: Optional[str] = None


class DeploymentRecordResponse(BaseModel):
    id: int
    code: str
    release_id: Optional[int]
    environment: str
    deployed_by: str
    deployed_at: datetime
    rollback_at: Optional[datetime]
    status: str
    notes: Optional[str]

    model_config = {"from_attributes": True}


# ─── UATSignOff ───────────────────────────────────────────────────────────


class UATSignOffCreate(BaseModel):
    code: str = Field(..., pattern=r"^FO-P4-\d{3}")
    release_id: Optional[int] = None
    project_id: Optional[int] = None
    signed_by: str
    comments: Optional[str] = None
    status: str = "pending"


class UATSignOffUpdate(BaseModel):
    comments: Optional[str] = None
    status: Optional[str] = None


class UATSignOffResponse(BaseModel):
    id: int
    code: str
    release_id: Optional[int]
    project_id: Optional[int]
    signed_by: str
    signed_at: datetime
    comments: Optional[str]
    status: str

    model_config = {"from_attributes": True}


# ─── SolutionSunset ───────────────────────────────────────────────────────


class SolutionSunsetCreate(BaseModel):
    code: str
    product: str
    sunset_date: date
    migration_path: str
    status: str = "planned"
    approved_by: str


class SolutionSunsetUpdate(BaseModel):
    sunset_date: Optional[date] = None
    migration_path: Optional[str] = None
    status: Optional[str] = None


class SolutionSunsetResponse(BaseModel):
    id: int
    code: str
    product: str
    sunset_date: date
    migration_path: str
    status: str
    approved_by: str
    created_at: datetime

    model_config = {"from_attributes": True}
