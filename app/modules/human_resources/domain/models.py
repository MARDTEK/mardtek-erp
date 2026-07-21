from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ─── Enums ────────────────────────────────────────────────────────────────

class PersonnelRequestStatus(str, enum.Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FILLED = "filled"


class InductionChecklistStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class IDPStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class EvaluationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    COMPLETED = "completed"


class IncidentType(str, enum.Enum):
    WARNING = "warning"
    ACCIDENT = "accident"
    VIOLATION = "violation"
    GRIEVANCE = "grievance"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ContractType(str, enum.Enum):
    PERMANENT = "permanent"
    CONTRACTOR = "contractor"
    INTERN = "intern"


class StaffStatus(str, enum.Enum):
    ACTIVE = "active"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"


# ─── Models ───────────────────────────────────────────────────────────────

class JobDescription(Base):
    """PER-P7-001 | Job Description — defines a role's responsibilities, requirements, and competencies."""

    __tablename__ = "hr_job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    reports_to: Mapped[Optional[str]] = mapped_column(String(255))
    responsibilities: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)
    competencies: Mapped[dict] = mapped_column(JSON, default=list)  # JSON list of competency names/levels
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<JobDescription {self.code} — {self.title}>"


class PersonnelRequest(Base):
    """FO-P7-001 | Personnel Request — formal request for headcount."""

    __tablename__ = "hr_personnel_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PersonnelRequestStatus] = mapped_column(
        Enum(PersonnelRequestStatus), default=PersonnelRequestStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<PersonnelRequest {self.code} — {self.job_title} [{self.status.value}]>"


class InductionChecklist(Base):
    """FO-P7-002 | Induction Checklist — tracks onboarding tasks for new hires."""

    __tablename__ = "hr_induction_checklists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    items: Mapped[dict] = mapped_column(
        JSON, default=list
    )  # JSON list of {item, completed_at, verified_by}
    status: Mapped[InductionChecklistStatus] = mapped_column(
        Enum(InductionChecklistStatus), default=InductionChecklistStatus.IN_PROGRESS
    )

    def __repr__(self) -> str:
        return f"<InductionChecklist {self.employee_name} [{self.status.value}]>"


class IndividualDevelopmentPlan(Base):
    """REG-P7-002 | Individual Development Plan — employee growth goals and courses."""

    __tablename__ = "hr_individual_development_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    goals: Mapped[dict] = mapped_column(JSON, default=list)  # JSON list of goal objects
    courses: Mapped[dict] = mapped_column(JSON, default=list)  # JSON list of course objects
    review_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[IDPStatus] = mapped_column(Enum(IDPStatus), default=IDPStatus.ACTIVE)

    def __repr__(self) -> str:
        return f"<IndividualDevelopmentPlan {self.employee_name} [{self.status.value}]>"


class PerformanceEvaluation(Base):
    """FO-P7-003 | Performance Evaluation — periodic employee performance review."""

    __tablename__ = "hr_performance_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    evaluator: Mapped[str] = mapped_column(String(255), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2026-H1"
    score: Mapped[Optional[int]] = mapped_column(Integer)  # 1–5
    strengths: Mapped[Optional[str]] = mapped_column(Text)
    improvements: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[EvaluationStatus] = mapped_column(
        Enum(EvaluationStatus), default=EvaluationStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<PerformanceEvaluation #{self.id} {self.employee_name} ({self.period}) [{self.status.value}]>"


class LaborIncident(Base):
    """FO-P7-004 | Labor Incident Report — warnings, accidents, violations, grievances."""

    __tablename__ = "hr_labor_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    incident_type: Mapped[IncidentType] = mapped_column(Enum(IncidentType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), default=IncidentStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<LaborIncident {self.code} [{self.incident_type.value}] {self.status.value}>"


class StaffRegister(Base):
    """REG-P7-001 | Staff Register — master record of all personnel."""

    __tablename__ = "hr_staff_register"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    contract_type: Mapped[ContractType] = mapped_column(Enum(ContractType), nullable=False)
    status: Mapped[StaffStatus] = mapped_column(Enum(StaffStatus), default=StaffStatus.ACTIVE)

    def __repr__(self) -> str:
        return f"<StaffRegister {self.employee_name} — {self.position} [{self.status.value}]>"
