from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import JSON, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────

class ProjectStatus(str, enum.Enum):
    KICKED_OFF = "kicked_off"
    IN_EXECUTION = "in_execution"
    CLOSED = "closed"
    ON_HOLD = "on_hold"


class ProductLine(str, enum.Enum):
    SERVICIOS = "SERVICIOS"
    SAAS = "SAAS"


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class CRStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class ChecklistStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class HandoverStatus(str, enum.Enum):
    PENDING = "pending"
    SIGNED = "signed"


class ClosureStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


# ─── Models ──────────────────────────────────────────────────────────────

class Project(Base):
    """Project master record — central entity for P5 execution lifecycle."""

    __tablename__ = "pmo_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("commercial_contracts.id")
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    product_line: Mapped[ProductLine] = mapped_column(Enum(ProductLine), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.KICKED_OFF)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    project_manager: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    execution_plans: Mapped[List[ProjectExecutionPlan]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    change_requests: Mapped[List[ChangeRequest]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    weekly_reports: Mapped[List[WeeklyProgressReport]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    deliverables_checklist: Mapped[Optional[DeliverablesChecklist]] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    follow_up_meetings: Mapped[List[FollowUpMeeting]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    handover_acceptance: Mapped[Optional[HandoverAcceptance]] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    closure_record: Mapped[Optional[ProjectClosureRecord]] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project {self.code} — {self.name} [{self.status.value}]>"


class ProjectExecutionPlan(Base):
    """PLN-P5-001 | Project Execution Plan — phases, milestones, and risks."""

    __tablename__ = "pmo_execution_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pmo_projects.id"), nullable=False
    )
    phases: Mapped[dict] = mapped_column(JSON, default=list)  # List of {name, start, end, status}
    milestones: Mapped[dict] = mapped_column(JSON, default=list)  # List of {name, target_date, completed_at}
    risks: Mapped[dict] = mapped_column(JSON, default=list)  # List of {description, impact, probability, mitigation}
    status: Mapped[PlanStatus] = mapped_column(Enum(PlanStatus, name="pmo_plan_status"), default=PlanStatus.DRAFT)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped[Project] = relationship(back_populates="execution_plans")

    def __repr__(self) -> str:
        return f"<ProjectExecutionPlan #{self.id} for Project #{self.project_id} [{self.status.value}]>"


class ChangeRequest(Base):
    """FO-P5-002 | Change Request Form — scope/schedule change requests."""

    __tablename__ = "pmo_change_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pmo_projects.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    impact_analysis: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[CRStatus] = mapped_column(Enum(CRStatus), default=CRStatus.SUBMITTED)
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped[Project] = relationship(back_populates="change_requests")

    def __repr__(self) -> str:
        return f"<ChangeRequest {self.code} [{self.status.value}]>"


class WeeklyProgressReport(Base):
    """INF-P5-001 | Weekly Progress Report — periodic status tracking."""

    __tablename__ = "pmo_weekly_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pmo_projects.id"), nullable=False
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    accomplishments: Mapped[str] = mapped_column(Text, nullable=False)
    next_week_plan: Mapped[str] = mapped_column(Text, nullable=False)
    blockers: Mapped[Optional[str]] = mapped_column(Text)
    status_percent: Mapped[int] = mapped_column(Integer, default=0)  # 0–100

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped[Project] = relationship(back_populates="weekly_reports")

    def __repr__(self) -> str:
        return f"<WeeklyProgressReport W{self.week_number}/{self.year} — {self.status_percent}%>"


class DeliverablesChecklist(Base):
    """FO-P5-003 | Deliverables Checklist — tracks project deliverable completion."""

    __tablename__ = "pmo_deliverables_checklists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pmo_projects.id"), unique=True, nullable=False
    )
    items: Mapped[dict] = mapped_column(JSON, default=list)  # List of {name, description, due_date, completed_at, verified_by}
    status: Mapped[ChecklistStatus] = mapped_column(
        Enum(ChecklistStatus), default=ChecklistStatus.IN_PROGRESS
    )

    project: Mapped[Project] = relationship(back_populates="deliverables_checklist")

    def __repr__(self) -> str:
        return f"<DeliverablesChecklist for Project #{self.project_id} [{self.status.value}]>"


class FollowUpMeeting(Base):
    """FO-P5-004 | Follow-Up Meeting Minutes — recurring progress meetings."""

    __tablename__ = "pmo_follow_up_meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pmo_projects.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    minutes: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[dict] = mapped_column(JSON, default=list)  # List of {action, responsible, deadline, status}
    next_meeting_date: Mapped[Optional[date]] = mapped_column(Date)

    project: Mapped[Project] = relationship(back_populates="follow_up_meetings")

    def __repr__(self) -> str:
        return f"<FollowUpMeeting #{self.id} for Project #{self.project_id} on {self.date}>"


class HandoverAcceptance(Base):
    """FO-P5-005 | Handover Acceptance Form — signed handover to customer."""

    __tablename__ = "pmo_handover_acceptances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pmo_projects.id"), unique=True, nullable=False
    )
    accepted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    comments: Mapped[Optional[str]] = mapped_column(Text)
    warranty_period_days: Mapped[int] = mapped_column(Integer, default=90)
    status: Mapped[HandoverStatus] = mapped_column(Enum(HandoverStatus), default=HandoverStatus.PENDING)

    project: Mapped[Project] = relationship(back_populates="handover_acceptance")

    def __repr__(self) -> str:
        return f"<HandoverAcceptance for Project #{self.project_id} [{self.status.value}]>"


class ProjectClosureRecord(Base):
    """REG-P5-001 | Project Closure Record — formal closure documentation."""

    __tablename__ = "pmo_closure_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pmo_projects.id"), unique=True, nullable=False
    )
    closed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text)
    final_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    customer_feedback: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ClosureStatus] = mapped_column(Enum(ClosureStatus), default=ClosureStatus.OPEN)

    project: Mapped[Project] = relationship(back_populates="closure_record")

    def __repr__(self) -> str:
        return f"<ProjectClosureRecord for Project #{self.project_id} [{self.status.value}]>"
