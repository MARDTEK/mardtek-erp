from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Infrastructure Request ──────────────────────────────────────────────

class InfrastructureRequestCreate(BaseModel):
    code: str
    requester: str
    resource_type: str  # server, license, network, tool, other
    specification: str
    justification: str


class InfrastructureRequestUpdate(BaseModel):
    specification: Optional[str] = None
    justification: Optional[str] = None


class InfrastructureRequestResponse(BaseModel):
    id: int
    code: str
    requester: str
    resource_type: str
    specification: str
    justification: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── SLA Agreement ───────────────────────────────────────────────────────

class SlaAgreementCreate(BaseModel):
    code: str
    provider: str
    service: str
    uptime_target: float = Field(..., ge=0, le=100)
    response_time_minutes: int = Field(..., gt=0)
    resolution_time_minutes: int = Field(..., gt=0)
    start_date: date
    end_date: date


class SlaAgreementUpdate(BaseModel):
    uptime_target: Optional[float] = Field(None, ge=0, le=100)
    response_time_minutes: Optional[int] = Field(None, gt=0)
    resolution_time_minutes: Optional[int] = Field(None, gt=0)
    status: Optional[str] = None


class SlaAgreementResponse(BaseModel):
    id: int
    code: str
    provider: str
    service: str
    uptime_target: float
    response_time_minutes: int
    resolution_time_minutes: int
    status: str
    start_date: date
    end_date: date

    model_config = {"from_attributes": True}


# ─── Incident Report ─────────────────────────────────────────────────────

class IncidentReportCreate(BaseModel):
    code: str
    service: str
    severity: str  # P1, P2, P3, P4
    description: str


class IncidentReportUpdate(BaseModel):
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    status: Optional[str] = None


class IncidentReportResponse(BaseModel):
    id: int
    code: str
    service: str
    severity: str
    description: str
    root_cause: Optional[str]
    resolution: Optional[str]
    status: str
    resolved_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Availability Report ─────────────────────────────────────────────────

class AvailabilityReportCreate(BaseModel):
    service: str
    period_start: datetime
    period_end: datetime
    uptime_percent: float = Field(..., ge=0, le=100)
    downtime_minutes: int = Field(..., ge=0)
    sla_met: bool


class AvailabilityReportResponse(BaseModel):
    id: int
    service: str
    period_start: datetime
    period_end: datetime
    uptime_percent: float
    downtime_minutes: int
    sla_met: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Business Continuity Plan ────────────────────────────────────────────

class BusinessContinuityPlanCreate(BaseModel):
    code: str
    title: str
    last_reviewed: date
    risk_assessment: Dict[str, Any]
    recovery_strategies: Dict[str, Any]


class BusinessContinuityPlanUpdate(BaseModel):
    title: Optional[str] = None
    version: Optional[str] = None
    last_reviewed: Optional[date] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    recovery_strategies: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class BusinessContinuityPlanResponse(BaseModel):
    id: int
    code: str
    title: str
    version: str
    last_reviewed: date
    risk_assessment: Dict[str, Any]
    recovery_strategies: Dict[str, Any]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Security Incident ───────────────────────────────────────────────────

class SecurityIncidentCreate(BaseModel):
    code: str
    incident_type: str  # breach, malware, phishing, unauthorized_access, other
    description: str
    impact: str
    containment: str


class SecurityIncidentUpdate(BaseModel):
    description: Optional[str] = None
    impact: Optional[str] = None
    containment: Optional[str] = None
    status: Optional[str] = None


class SecurityIncidentResponse(BaseModel):
    id: int
    code: str
    incident_type: str
    description: str
    impact: str
    containment: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Maintenance Record ──────────────────────────────────────────────────

class MaintenanceRecordCreate(BaseModel):
    asset: str
    maintenance_type: str  # preventive, corrective, upgrade
    description: str
    scheduled_date: date
    performed_by: Optional[str] = None


class MaintenanceRecordUpdate(BaseModel):
    description: Optional[str] = None
    completed_date: Optional[date] = None
    performed_by: Optional[str] = None
    status: Optional[str] = None


class MaintenanceStatusTransition(BaseModel):
    target_status: str
    performed_by: str | None = None
    completed_date: date | None = None


class MaintenanceRecordResponse(BaseModel):
    id: int
    asset: str
    maintenance_type: str
    description: str
    scheduled_date: date
    completed_date: Optional[date]
    performed_by: Optional[str]
    status: str

    model_config = {"from_attributes": True}
