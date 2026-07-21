from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────

class RequestStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PROVISIONED = "provisioned"
    REJECTED = "rejected"


class SlaStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class IncidentSeverity(str, enum.Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ContinuityPlanStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class SecurityIncidentType(str, enum.Enum):
    BREACH = "breach"
    MALWARE = "malware"
    PHISHING = "phishing"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    OTHER = "other"


class SecurityIncidentStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    UPGRADE = "upgrade"


class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ─── Models ──────────────────────────────────────────────────────────────

class InfrastructureRequest(Base):
    """FO-P8-001 | Infrastructure Request — request for servers, licenses,
    network, tools, or other technology resources."""

    __tablename__ = "infra_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    requester: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)  # server, license, network, tool, other
    specification: Mapped[str] = mapped_column(Text, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.SUBMITTED)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<InfrastructureRequest {self.code} [{self.resource_type}] {self.status.value}>"


class SlaAgreement(Base):
    """FO-P8-003 | SLA Agreement — service level agreement with a provider."""

    __tablename__ = "infra_sla_agreements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    service: Mapped[str] = mapped_column(String(255), nullable=False)
    uptime_target: Mapped[float] = mapped_column(Float, nullable=False)  # e.g. 99.9
    response_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SlaStatus] = mapped_column(Enum(SlaStatus), default=SlaStatus.ACTIVE)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    def __repr__(self) -> str:
        return f"<SlaAgreement {self.code} — {self.provider}/{self.service} [{self.status.value}]>"


class IncidentReport(Base):
    """FO-P8-002 | Incident Report — documents a service incident."""

    __tablename__ = "infra_incident_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    service: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(Enum(IncidentSeverity), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.OPEN)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<IncidentReport {self.code} [{self.severity.value}] {self.status.value}>"


class AvailabilityReport(Base):
    """INF-P8-001 | Availability Report — uptime and SLA compliance for a service."""

    __tablename__ = "infra_availability_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uptime_percent: Mapped[float] = mapped_column(Float, nullable=False)
    downtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    sla_met: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<AvailabilityReport {self.service} {self.period_start.date()} — {self.uptime_percent}%>"


class BusinessContinuityPlan(Base):
    """PLN-P8-001 | Business Continuity Plan — risk assessment and recovery strategies."""

    __tablename__ = "infra_continuity_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    last_reviewed: Mapped[date] = mapped_column(Date, nullable=False)
    risk_assessment: Mapped[dict] = mapped_column(JSON, nullable=False)
    recovery_strategies: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[ContinuityPlanStatus] = mapped_column(
        Enum(ContinuityPlanStatus), default=ContinuityPlanStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<BusinessContinuityPlan {self.code} v{self.version} [{self.status.value}]>"


class SecurityIncident(Base):
    """INF-P8-002 | Security Incident — tracks security breaches, malware, phishing, etc."""

    __tablename__ = "infra_security_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    incident_type: Mapped[SecurityIncidentType] = mapped_column(Enum(SecurityIncidentType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    containment: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SecurityIncidentStatus] = mapped_column(
        Enum(SecurityIncidentStatus), default=SecurityIncidentStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<SecurityIncident {self.code} [{self.incident_type.value}] {self.status.value}>"


class MaintenanceRecord(Base):
    """REG-P8-001 | Maintenance Record — tracks preventive, corrective, and upgrade maintenance."""

    __tablename__ = "infra_maintenance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset: Mapped[str] = mapped_column(String(255), nullable=False)
    maintenance_type: Mapped[MaintenanceType] = mapped_column(Enum(MaintenanceType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_date: Mapped[Optional[date]] = mapped_column(Date)
    performed_by: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[MaintenanceStatus] = mapped_column(
        Enum(MaintenanceStatus), default=MaintenanceStatus.SCHEDULED
    )

    def __repr__(self) -> str:
        return f"<MaintenanceRecord {self.asset} [{self.maintenance_type.value}] {self.status.value}>"
