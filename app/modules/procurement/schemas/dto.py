from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Purchase Request (FO-P9-001) ─────────────────────────────────────────

class PurchaseRequestCreate(BaseModel):
    code: str
    requester: str
    description: str
    quantity: float = Field(..., gt=0)
    estimated_cost: float = Field(..., ge=0)
    category: str
    justification: str


class PurchaseRequestUpdate(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    estimated_cost: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    justification: Optional[str] = None


class PurchaseRequestResponse(BaseModel):
    id: int
    code: str
    requester: str
    description: str
    quantity: float
    estimated_cost: float
    category: str
    justification: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Supplier Registration (FO-P9-002) ─────────────────────────────────────

class SupplierRegistrationCreate(BaseModel):
    code: str
    company_name: str
    contact: str
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    phone: str
    services: str


class SupplierRegistrationUpdate(BaseModel):
    company_name: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    phone: Optional[str] = None
    services: Optional[str] = None


class SupplierRegistrationResponse(BaseModel):
    id: int
    code: str
    company_name: str
    contact: str
    email: str
    phone: str
    services: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Supplier Evaluation (FO-P9-003) ───────────────────────────────────────

class CriteriaScores(BaseModel):
    quality: int = Field(..., ge=1, le=5)
    price: int = Field(..., ge=1, le=5)
    delivery: int = Field(..., ge=1, le=5)
    service: int = Field(..., ge=1, le=5)


class SupplierEvaluationCreate(BaseModel):
    supplier_id: int
    evaluator: str
    criteria_scores: CriteriaScores
    period: str  # e.g. "2026-Q1"


class SupplierEvaluationResponse(BaseModel):
    id: int
    supplier_id: int
    evaluator: str
    criteria_scores: Any  # dict from JSON column
    total_score: Optional[float]
    period: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Supplier Performance Report (INF-P9-001) ──────────────────────────────

class SupplierPerformanceReportCreate(BaseModel):
    supplier_id: int
    period: str
    avg_score: float = Field(..., ge=0, le=100)
    on_time_delivery_pct: float = Field(..., ge=0, le=100)
    quality_rating: float = Field(..., ge=0, le=100)
    notes: Optional[str] = None


class SupplierPerformanceReportResponse(BaseModel):
    id: int
    supplier_id: int
    period: str
    avg_score: float
    on_time_delivery_pct: float
    quality_rating: float
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Receiving Report (FO-P9-004) ──────────────────────────────────────────

class ReceivingReportCreate(BaseModel):
    purchase_request_id: Optional[int] = None
    received_by: str
    items: List[Dict[str, Any]]
    received_date: datetime
    condition_ok: bool
    notes: Optional[str] = None


class ReceivingReportResponse(BaseModel):
    id: int
    purchase_request_id: Optional[int]
    received_by: str
    items: Any
    received_date: datetime
    condition_ok: bool
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Supplier Register (REG-P9-001) ────────────────────────────────────────

class SupplierRegisterCreate(BaseModel):
    supplier_id: int
    approved_by: str
    category: str


class SupplierRegisterResponse(BaseModel):
    id: int
    supplier_id: int
    approved_at: datetime
    approved_by: str
    category: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SupplierRegisterUpdate(BaseModel):
    category: Optional[str] = None
    is_active: Optional[bool] = None
