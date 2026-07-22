from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────

class IndicatorStatus(str, enum.Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    ACHIEVED = "achieved"


class Frequency(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TrendDirection(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    FLAT = "flat"
    VOLATILE = "volatile"


# ─── Models ──────────────────────────────────────────────────────────────

class PerformanceIndicator(Base):
    """MAT-P11-001 | Performance Indicators Matrix — defines measurable KPIs across all SGC processes."""

    __tablename__ = "analytics_performance_indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)  # e.g. KPI-P2-001
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    process_code: Mapped[str] = mapped_column(String(3), nullable=False)  # P1–P11
    formula: Mapped[Optional[str]] = mapped_column(Text)
    target_value: Mapped[Optional[float]] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    frequency: Mapped[Frequency] = mapped_column(Enum(Frequency), default=Frequency.MONTHLY)
    owner: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    data_records: Mapped[List[PerformanceDataRecord]] = relationship(
        back_populates="indicator", cascade="all, delete-orphan"
    )
    trend_reports: Mapped[List[TrendAnalysisReport]] = relationship(
        back_populates="indicator", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PerformanceIndicator {self.code} [{self.process_code}] {'active' if self.is_active else 'inactive'}>"


class PerformanceDataRecord(Base):
    """REG-P11-001 | Performance Data Record — individual data point for a KPI."""

    __tablename__ = "analytics_performance_data_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analytics_performance_indicators.id"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM for monthly, YYYY for yearly
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    recorded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    indicator: Mapped[PerformanceIndicator] = relationship(back_populates="data_records")

    def __repr__(self) -> str:
        return f"<PerformanceDataRecord #{self.id} I{self.indicator_id} {self.period} = {self.value}>"


class KpiReport(Base):
    """INF-P11-001 | KPI Report — periodic consolidated report with indicator statuses."""

    __tablename__ = "analytics_kpi_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    indicators_data: Mapped[Optional[Any]] = mapped_column(JSON)  # list of {indicator_id, name, value, target, status}
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<KpiReport {self.code} [{self.period_start} – {self.period_end}]>"


class PerformanceDashboard(Base):
    """INF-P11-002 | Performance Dashboard — configurable dashboard with layout and filters."""

    __tablename__ = "analytics_performance_dashboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    layout: Mapped[Optional[Any]] = mapped_column(JSON)
    filters: Mapped[Optional[Any]] = mapped_column(JSON)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<PerformanceDashboard {self.code} — {self.title}>"


class TrendAnalysisReport(Base):
    """INF-P11-003 | Trend Analysis Report — direction, volatility, and insights per indicator."""

    __tablename__ = "analytics_trend_analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    indicator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analytics_performance_indicators.id"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    trend: Mapped[TrendDirection] = mapped_column(Enum(TrendDirection), nullable=False)
    change_percent: Mapped[Optional[float]] = mapped_column(Float)
    insights: Mapped[Optional[str]] = mapped_column(Text)
    recommendations: Mapped[Optional[str]] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    indicator: Mapped[PerformanceIndicator] = relationship(back_populates="trend_reports")

    def __repr__(self) -> str:
        return f"<TrendAnalysisReport {self.code} [{self.trend.value}] I{self.indicator_id}>"
