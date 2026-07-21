from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum, Float, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────

class PolicyStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    OBSOLETE = "obsolete"


class ObjectiveStatus(str, enum.Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BEHIND = "behind"
    ACHIEVED = "achieved"


class MarketingPlanStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


# ─── Models ──────────────────────────────────────────────────────────────

class QualityPolicy(Base):
    """POL-P1-001 | Quality Policy — strategic quality commitment statement."""

    __tablename__ = "strategic_quality_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    status: Mapped[PolicyStatus] = mapped_column(Enum(PolicyStatus), default=PolicyStatus.DRAFT)

    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<QualityPolicy {self.code} v{self.version} [{self.status.value}]>"


class QualityObjective(Base):
    """MAT-P1-001 | Quality Objectives Matrix — measurable goals per process."""

    __tablename__ = "strategic_quality_objectives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    process_code: Mapped[str] = mapped_column(String(3), nullable=False)  # P1–P11

    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[Optional[float]] = mapped_column(Float)
    metric_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[ObjectiveStatus] = mapped_column(Enum(ObjectiveStatus), default=ObjectiveStatus.ON_TRACK)
    responsible: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<QualityObjective {self.code} [{self.status.value}] {self.process_code}>"


class MarketingPlan(Base):
    """PLN-P1-001 | Annual Marketing Plan — strategic marketing activities."""

    __tablename__ = "strategic_marketing_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    goals: Mapped[str] = mapped_column(Text, nullable=False)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    activities: Mapped[dict] = mapped_column(JSON, default=list)

    status: Mapped[MarketingPlanStatus] = mapped_column(
        Enum(MarketingPlanStatus), default=MarketingPlanStatus.DRAFT
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<MarketingPlan {self.code} ({self.year}) [{self.status.value}]>"


class StrategyReview(Base):
    """FO-P1-001 | Strategy Review Form — periodic strategic alignment review."""

    __tablename__ = "strategic_strategy_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    reviewed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    decisions: Mapped[str] = mapped_column(Text, nullable=False)
    next_review_date: Mapped[Optional[date]] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<StrategyReview {self.date} by {self.reviewed_by}>"


class ManagementReviewReport(Base):
    """INF-P1-001 | Management Review Report — top-level QMS performance review."""

    __tablename__ = "strategic_management_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    review_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    review_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    prepared_by: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    conclusions: Mapped[dict] = mapped_column(JSON, default=dict)
    report_url: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<ManagementReviewReport {self.code}: {self.title}>"


class QmsScope(Base):
    """PL-P1-001 | QMS Scope Definition — organizational scope and exclusions."""

    __tablename__ = "strategic_qms_scope"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    scope_description: Mapped[str] = mapped_column(Text, nullable=False)
    exclusions: Mapped[Optional[str]] = mapped_column(Text)
    applicable_normative: Mapped[str] = mapped_column(Text, nullable=False)

    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<QmsScope v{self.version} [{'current' if self.is_current else 'archived'}]>"
