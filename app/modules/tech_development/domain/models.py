"""P4 — Design & Development of Solutions: SQLAlchemy models."""

from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Enums ────────────────────────────────────────────────────────────────


class ProductLine(str, enum.Enum):
    SERVICIOS = "SERVICIOS"
    SAAS = "SAAS"


class RoadmapStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class ReleaseStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"


class SpecStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class TestType(str, enum.Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    REGRESSION = "regression"


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    FINAL = "final"


class DeploymentEnvironment(str, enum.Enum):
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class UATStatus(str, enum.Enum):
    PENDING = "pending"
    SIGNED = "signed"
    REJECTED = "rejected"


class SunsetStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ─── Models ───────────────────────────────────────────────────────────────


class ProductRoadmap(Base):
    """PLN-P4-001 | Product Roadmap — strategic vision and planned items."""

    __tablename__ = "tech_product_roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    product_line: Mapped[ProductLine] = mapped_column(Enum(ProductLine), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    vision: Mapped[str] = mapped_column(Text, nullable=False)
    strategic_goals: Mapped[str] = mapped_column(Text, nullable=False)
    items: Mapped[dict] = mapped_column(JSON, default=list)  # [{title, quarter, status, owner}]
    status: Mapped[RoadmapStatus] = mapped_column(Enum(RoadmapStatus), default=RoadmapStatus.DRAFT)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<ProductRoadmap {self.code} {self.year} [{self.product_line.value}] {self.status.value}>"


class ReleasePlan(Base):
    """PLN-P4-002 | Release Plan — scheduled version deployments."""

    __tablename__ = "tech_release_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    product: Mapped[str] = mapped_column(String(100), nullable=False)
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_date: Mapped[Optional[date]] = mapped_column(Date)
    features: Mapped[dict] = mapped_column(JSON, default=list)  # [{id, title, status}]
    status: Mapped[ReleaseStatus] = mapped_column(Enum(ReleaseStatus), default=ReleaseStatus.PLANNED)
    release_notes: Mapped[Optional[str]] = mapped_column(Text)

    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    deployments: Mapped[list["DeploymentRecord"]] = relationship(
        back_populates="release", cascade="all, delete-orphan"
    )
    uat_signoffs: Mapped[list["UATSignOff"]] = relationship(
        back_populates="release", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ReleasePlan {self.code} v{self.version} [{self.status.value}]>"


class TechnicalSpecification(Base):
    """Technical Specification — architecture and design docs for SERVICIOS/SAAS."""

    __tablename__ = "tech_technical_specs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)  # for SERVICIOS
    product: Mapped[Optional[str]] = mapped_column(String(100))  # for SAAS
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SpecStatus] = mapped_column(Enum(SpecStatus), default=SpecStatus.DRAFT)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<TechnicalSpecification {self.code} v{self.version} [{self.status.value}]>"


class RiskMatrix(Base):
    """MAT-P4-001 | Risk Matrix — technical and project risks."""

    __tablename__ = "tech_risk_matrices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    risks: Mapped[dict] = mapped_column(JSON, default=list)  # [{id, description, probability, impact, mitigation, owner, status}]
    version: Mapped[str] = mapped_column(String(10), default="1.0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<RiskMatrix {self.code} v{self.version}>"


class QATestReport(Base):
    """INF-P4-001 | QA Test Report — test execution results."""

    __tablename__ = "tech_qa_test_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    release_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tech_release_plans.id")
    )
    test_type: Mapped[TestType] = mapped_column(Enum(TestType), nullable=False)
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[int] = mapped_column(Integer, nullable=False)
    failed: Mapped[int] = mapped_column(Integer, nullable=False)
    blocked: Mapped[int] = mapped_column(Integer, default=0)
    report_url: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.DRAFT)

    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<QATestReport {self.code} {self.test_type.value} {self.passed}/{self.total_tests}>"


class DeploymentRecord(Base):
    """REG-P4-001 | Deployment Record — log of environment deployments."""

    __tablename__ = "tech_deployment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    release_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tech_release_plans.id")
    )
    environment: Mapped[DeploymentEnvironment] = mapped_column(Enum(DeploymentEnvironment), nullable=False)
    deployed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    rollback_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[DeploymentStatus] = mapped_column(Enum(DeploymentStatus), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationship
    release: Mapped[Optional[ReleasePlan]] = relationship(back_populates="deployments")

    def __repr__(self) -> str:
        return f"<DeploymentRecord {self.code} {self.environment.value} [{self.status.value}]>"


class UATSignOff(Base):
    """FO-P4-001 | UAT Sign-Off — user acceptance approval."""

    __tablename__ = "tech_uat_signoffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    release_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tech_release_plans.id")
    )
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    signed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    comments: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[UATStatus] = mapped_column(Enum(UATStatus), default=UATStatus.PENDING)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationship
    release: Mapped[Optional[ReleasePlan]] = relationship(back_populates="uat_signoffs")

    def __repr__(self) -> str:
        return f"<UATSignOff {self.code} [{self.status.value}]>"


class SolutionSunset(Base):
    """Solution Sunset Plan — end-of-life and migration planning."""

    __tablename__ = "tech_solution_sunsets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    product: Mapped[str] = mapped_column(String(100), nullable=False)
    sunset_date: Mapped[date] = mapped_column(Date, nullable=False)
    migration_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SunsetStatus] = mapped_column(Enum(SunsetStatus), default=SunsetStatus.PLANNED)
    approved_by: Mapped[str] = mapped_column(String(255), nullable=False)

    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<SolutionSunset {self.code} {self.product} [{self.status.value}]>"
