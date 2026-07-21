from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────

class NpsCategory(str, enum.Enum):
    PROMOTER = "promoter"
    PASSIVE = "passive"
    DETRACTOR = "detractor"


class ComplaintType(str, enum.Enum):
    COMPLAINT = "complaint"
    CLAIM = "claim"


class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EscalationLevel(int, enum.Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


class ChurnReasonCategory(str, enum.Enum):
    PRICE = "price"
    PRODUCT_FIT = "product_fit"
    SUPPORT = "support"
    PERFORMANCE = "performance"
    COMPETITOR = "competitor"
    OTHER = "other"


# ─── Models ──────────────────────────────────────────────────────────────

class NpsSurvey(Base):
    """FO-P10-001 | NPS Survey — for SAAS (MicroSmart). Score 0-10."""

    __tablename__ = "cx_nps_surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0–10
    category: Mapped[NpsCategory] = mapped_column(Enum(NpsCategory), nullable=False)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<NpsSurvey {self.code} score={self.score} [{self.category.value}]>"


class CsatSurvey(Base):
    """FO-P10-002 | CSAT Survey — for SERVICIOS. Score 1-5."""

    __tablename__ = "cx_csat_surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–5
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<CsatSurvey {self.code} score={self.score}>"


class CesSurvey(Base):
    """FO-P10-003 | CES Survey — for SAAS. Score 1-7."""

    __tablename__ = "cx_ces_surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–7
    task_description: Mapped[str] = mapped_column(String(500), nullable=False)
    responded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<CesSurvey {self.code} score={self.score}>"


class ComplaintClaim(Base):
    """FO-P10-004 | Complaint/Claims Form — tracks issues linked to P2 NCs."""

    __tablename__ = "cx_complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    type: Mapped[ComplaintType] = mapped_column(Enum(ComplaintType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    desired_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus), default=ComplaintStatus.OPEN
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    escalation_level: Mapped[int] = mapped_column(Integer, default=1)  # 1–3
    nc_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Linked to P2
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<ComplaintClaim {self.code} [{self.type.value}] {self.status.value}>"


class ComplaintRegister(Base):
    """REG-P10-001 | Complaint Register — consolidated record per complaint."""

    __tablename__ = "cx_complaint_register"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cx_complaints.id"), unique=True, nullable=False
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    resolution_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<ComplaintRegister complaint={self.complaint_id} {self.category}>"


class ExitInterview(Base):
    """FO-P10-005 | Exit Interview — churn analysis for SAAS subscribers."""

    __tablename__ = "cx_exit_interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    subscription_id: Mapped[int] = mapped_column(Integer, nullable=False)
    churn_reason_category: Mapped[ChurnReasonCategory] = mapped_column(
        Enum(ChurnReasonCategory), nullable=False
    )
    detailed_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    would_return: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    interview_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return (
            f"<ExitInterview {self.code} reason={self.churn_reason_category.value}>"
        )


class SatisfactionReport(Base):
    """INF-P10-001 | Customer Satisfaction Report — periodic aggregated summary."""

    __tablename__ = "cx_satisfaction_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. 2026-Q2
    nps_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    csat_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ces_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    complaints_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<SatisfactionReport {self.code} period={self.period}>"
