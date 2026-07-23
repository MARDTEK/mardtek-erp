from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────

class NeedPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NeedStatus(str, enum.Enum):
    IDENTIFIED = "identified"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    COMPLETED = "completed"


class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseModality(str, enum.Enum):
    ONLINE = "online"
    PRESENTIAL = "presential"
    HYBRID = "hybrid"


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class SessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CertStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ManualStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class VideoStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ─── Models ──────────────────────────────────────────────────────────────

class TrainingNeedsAssessment(Base):
    """FO-P6-001 | Training Needs Assessment — identifies skills gaps per role."""

    __tablename__ = "training_needs_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    skills_gap: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[NeedPriority] = mapped_column(Enum(NeedPriority), default=NeedPriority.MEDIUM)
    status: Mapped[NeedStatus] = mapped_column(Enum(NeedStatus), default=NeedStatus.IDENTIFIED)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<TrainingNeedsAssessment {self.code} [{self.priority.value}] {self.employee_name}>"


class CompetencyMatrix(Base):
    """MAT-P6-001 | Competency Matrix — maps required vs current competency levels per role."""

    __tablename__ = "training_competency_matrices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    competencies: Mapped[dict] = mapped_column(JSON, default=list)  # [{name, required_level, current_level, gap}]
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    is_active: Mapped[bool] = mapped_column(default=True)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    def __repr__(self) -> str:
        return f"<CompetencyMatrix {self.code} v{self.version} [{self.role}]>"


class Course(Base):
    """SOP-P6-002 | Course — designed training content with modality and duration."""

    __tablename__ = "training_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    modality: Mapped[CourseModality] = mapped_column(Enum(CourseModality), nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Commercial fields
    is_sellable: Mapped[bool] = mapped_column(Boolean, default=False)
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    
    status: Mapped[CourseStatus] = mapped_column(Enum(CourseStatus), default=CourseStatus.DRAFT)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    sessions: Mapped[list[TrainingSession]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course {self.code} — {self.title} [{self.modality.value}]>"


class TrainingPlan(Base):
    """PLN-P6-001 | Annual Training Plan — groups courses by year with budget."""

    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    courses: Mapped[dict] = mapped_column(JSON, default=list)  # List of course codes or ids
    budget: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[PlanStatus] = mapped_column(Enum(PlanStatus), default=PlanStatus.DRAFT)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    def __repr__(self) -> str:
        return f"<TrainingPlan {self.code} [{self.year}] {self.status.value}>"


class TrainingSession(Base):
    """SOP-P6-003 | Training Session — scheduled delivery of a course."""

    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_courses.id"), nullable=False, index=True
    )
    instructor: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    attendees: Mapped[dict] = mapped_column(JSON, default=list)  # List of participant names
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    course: Mapped[Course] = relationship(back_populates="sessions")
    evaluations: Mapped[list[TrainingEvaluation]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    attendance_records: Mapped[list[AttendanceRecord]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TrainingSession #{self.id} [{self.status.value}] course={self.course_id}>"


class TrainingEvaluation(Base):
    """FO-P6-002 | Training Evaluation — participant feedback on a session."""

    __tablename__ = "training_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_sessions.id"), nullable=False, index=True
    )
    participant: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    session: Mapped[TrainingSession] = relationship(back_populates="evaluations")

    def __repr__(self) -> str:
        return f"<TrainingEvaluation #{self.id} [{self.score}/5] session={self.session_id}>"


class AttendanceRecord(Base):
    """REG-P6-001 | Attendance Record — participant attendance per session."""

    __tablename__ = "training_attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_sessions.id"), nullable=False, index=True
    )
    participant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hours_attended: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    session: Mapped[TrainingSession] = relationship(back_populates="attendance_records")

    def __repr__(self) -> str:
        return f"<AttendanceRecord #{self.id} — {self.participant_name} [{self.hours_attended}h]>"


class CertificationRecord(Base):
    """REG-P6-002 | Certification Record — tracks issued certificates for completed training."""

    __tablename__ = "training_certification_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    participant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_courses.id"), nullable=False, index=True
    )
    certificate_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[CertStatus] = mapped_column(Enum(CertStatus), default=CertStatus.ACTIVE)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    course: Mapped[Course] = relationship()

    def __repr__(self) -> str:
        return f"<CertificationRecord {self.certificate_code} [{self.status.value}] — {self.participant_name}>"


class UserManual(Base):
    """MAN-P6-001 | User Manual — product documentation for external customers."""

    __tablename__ = "training_user_manuals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    product: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    content_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ManualStatus] = mapped_column(Enum(ManualStatus), default=ManualStatus.DRAFT)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    def __repr__(self) -> str:
        return f"<UserManual {self.code} v{self.version} — {self.title}>"


class VideoTutorial(Base):
    """GUIA-P6-001 | Video Tutorial — instructional video for a course or product."""

    __tablename__ = "training_video_tutorials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    course_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("training_courses.id"), nullable=True, index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[VideoStatus] = mapped_column(Enum(VideoStatus), default=VideoStatus.DRAFT)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    def __repr__(self) -> str:
        return f"<VideoTutorial {self.code} — {self.title} [{self.duration_minutes}min]>"
