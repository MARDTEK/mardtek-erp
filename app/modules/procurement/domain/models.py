from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────

class PurchaseRequestStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ORDERED = "ordered"
    CANCELLED = "cancelled"


class SupplierStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class EvaluationStatus(str, enum.Enum):
    DRAFT = "draft"
    COMPLETED = "completed"


# ─── Models ──────────────────────────────────────────────────────────────

class PurchaseRequest(Base):
    """FO-P9-001 | Purchase Request Form — initiates procurement."""

    __tablename__ = "procurement_purchase_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    requester: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[PurchaseRequestStatus] = mapped_column(
        Enum(PurchaseRequestStatus), default=PurchaseRequestStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    receiving_reports: Mapped[List[ReceivingReport]] = relationship(
        back_populates="purchase_request", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PurchaseRequest {self.code} [{self.status.value}] {self.requester}>"


class SupplierRegistration(Base):
    """FO-P9-002 | Supplier Registration Form — captures supplier data."""

    __tablename__ = "procurement_supplier_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    services: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SupplierStatus] = mapped_column(
        Enum(SupplierStatus), default=SupplierStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    evaluations: Mapped[List[SupplierEvaluation]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    performance_reports: Mapped[List[SupplierPerformanceReport]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    register_entry: Mapped[Optional[SupplierRegister]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<SupplierRegistration {self.code} — {self.company_name} [{self.status.value}]>"


class SupplierEvaluation(Base):
    """FO-P9-003 | Supplier Evaluation Form — scores supplier performance."""

    __tablename__ = "procurement_supplier_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("procurement_supplier_registrations.id"), nullable=False
    )
    evaluator: Mapped[str] = mapped_column(String(255), nullable=False)
    criteria_scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_score: Mapped[Optional[float]] = mapped_column(Float)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2026-Q1"
    status: Mapped[EvaluationStatus] = mapped_column(
        Enum(EvaluationStatus, name="proc_evaluation_status"), default=EvaluationStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    supplier: Mapped[SupplierRegistration] = relationship(back_populates="evaluations")

    def __repr__(self) -> str:
        return f"<SupplierEvaluation #{self.id} supplier={self.supplier_id} [{self.status.value}]>"


class SupplierPerformanceReport(Base):
    """INF-P9-001 | Supplier Performance Report — aggregated metrics."""

    __tablename__ = "procurement_supplier_performance_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("procurement_supplier_registrations.id"), nullable=False
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    avg_score: Mapped[float] = mapped_column(Float, nullable=False)
    on_time_delivery_pct: Mapped[float] = mapped_column(Float, nullable=False)
    quality_rating: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    supplier: Mapped[SupplierRegistration] = relationship(back_populates="performance_reports")

    def __repr__(self) -> str:
        return f"<SupplierPerformanceReport #{self.id} supplier={self.supplier_id} {self.period}>"


class ReceivingReport(Base):
    """FO-P9-004 | Receiving Report — records goods/services receipt."""

    __tablename__ = "procurement_receiving_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_request_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("procurement_purchase_requests.id"), nullable=True
    )
    received_by: Mapped[str] = mapped_column(String(255), nullable=False)
    items: Mapped[dict] = mapped_column(JSON, nullable=False)
    received_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    condition_ok: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    purchase_request: Mapped[Optional[PurchaseRequest]] = relationship(
        back_populates="receiving_reports"
    )

    def __repr__(self) -> str:
        return f"<ReceivingReport #{self.id} by {self.received_by}>"


class SupplierRegister(Base):
    """REG-P9-001 | Supplier Register — approved supplier master list."""

    __tablename__ = "procurement_supplier_register"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("procurement_supplier_registrations.id"), unique=True, nullable=False
    )
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    approved_by: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    supplier: Mapped[SupplierRegistration] = relationship(back_populates="register_entry")

    def __repr__(self) -> str:
        return f"<SupplierRegister #{self.id} — {self.category} active={self.is_active}>"
