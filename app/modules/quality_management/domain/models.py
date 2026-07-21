from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────

class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    OBSOLETE = "obsolete"


class NCSeverity(str, enum.Enum):
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class NCStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CORRECTIVE_ACTION = "corrective_action"
    VERIFICATION = "verification"
    CLOSED = "closed"


class ActionStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"


class AuditStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AuditResult(str, enum.Enum):
    PASS = "pass"
    MINOR_NC = "minor_nc"
    MAJOR_NC = "major_nc"
    CRITICAL_NC = "critical_nc"


class ImprovementStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    EVALUATED = "evaluated"


# ─── Models ──────────────────────────────────────────────────────────────

class Document(Base):
    """REG-P2-001 | Document Master List — controls all SGC documented info."""

    __tablename__ = "quality_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    process_code: Mapped[str] = mapped_column(String(3), nullable=False)  # P1–P11
    doc_type: Mapped[str] = mapped_column(String(10), nullable=False)  # SOP, FO, REG, etc.

    version: Mapped[str] = mapped_column(String(10), default="1.0")
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)

    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[Optional[date]] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Document {self.code} v{self.version} [{self.status.value}]>"


class NonConformity(Base):
    """FO-P2-002 | Non-Conformity Report — tracks NCs from any source."""

    __tablename__ = "quality_non_conformities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    source: Mapped[str] = mapped_column(String(50), nullable=False)  # audit, complaint, internal, supplier
    source_ref: Mapped[Optional[str]] = mapped_column(String(50))  # e.g. audit_id or complaint_id

    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[NCSeverity] = mapped_column(Enum(NCSeverity), nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[NCStatus] = mapped_column(Enum(NCStatus), default=NCStatus.OPEN)

    reported_by: Mapped[str] = mapped_column(String(255), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationship
    corrective_actions: Mapped[List[CorrectiveAction]] = relationship(
        back_populates="non_conformity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<NonConformity {self.code} [{self.severity.value}] {self.status.value}>"


class CorrectiveAction(Base):
    """FO-P2-003 | Corrective Action Request — CAPA linked to an NC."""

    __tablename__ = "quality_corrective_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    nc_id: Mapped[int] = mapped_column(Integer, ForeignKey("quality_non_conformities.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    responsible: Mapped[str] = mapped_column(String(255), nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)

    implementation_evidence: Mapped[Optional[str]] = mapped_column(Text)
    effectiveness_review: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ActionStatus] = mapped_column(Enum(ActionStatus), default=ActionStatus.OPEN)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    non_conformity: Mapped[NonConformity] = relationship(back_populates="corrective_actions")

    def __repr__(self) -> str:
        return f"<CorrectiveAction {self.code} [{self.status.value}]>"


class InternalAudit(Base):
    """REG-P2-002 | Audit Schedule — planned and completed audits."""

    __tablename__ = "quality_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    audit_date: Mapped[Optional[date]] = mapped_column(Date)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    auditor: Mapped[str] = mapped_column(String(255), nullable=False)
    audited_process: Mapped[str] = mapped_column(String(3), nullable=False)  # P1–P11

    status: Mapped[AuditStatus] = mapped_column(Enum(AuditStatus), default=AuditStatus.PLANNED)
    result: Mapped[Optional[AuditResult]] = mapped_column(Enum(AuditResult))

    findings_summary: Mapped[Optional[str]] = mapped_column(Text)
    report_url: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    checklist_items: Mapped[List[AuditChecklistItem]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<InternalAudit {self.code} [{self.status.value}] {self.audited_process}>"


class AuditChecklistItem(Base):
    """FO-P2-001 | Audit Checklist — individual question/verification."""

    __tablename__ = "quality_audit_checklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quality_audits.id"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[Optional[str]] = mapped_column(String(20))  # pass, fail, na
    evidence: Mapped[Optional[str]] = mapped_column(Text)
    nc_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quality_non_conformities.id")
    )

    audit: Mapped[InternalAudit] = relationship(back_populates="checklist_items")

    def __repr__(self) -> str:
        return f"<AuditChecklistItem #{self.id} [{self.result or 'pending'}]>"


class ProcessOwner(Base):
    """MAT-P2-001 | Process Owner Assignment Matrix."""

    __tablename__ = "quality_process_owners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)  # P1–P11
    process_name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    since_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<ProcessOwner {self.process_code} — {self.owner_name}>"


class ContinuousImprovement(Base):
    """SOP-P2-006 | Continuous Improvement — tracks improvement proposals."""

    __tablename__ = "quality_improvements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    source: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. audit, suggestion, data
    source_ref: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_benefit: Mapped[Optional[str]] = mapped_column(Text)

    responsible: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ImprovementStatus] = mapped_column(
        Enum(ImprovementStatus), default=ImprovementStatus.PROPOSED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    implemented_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<ContinuousImprovement {self.code} [{self.status.value}]>"
