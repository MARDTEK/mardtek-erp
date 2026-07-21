from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Training Needs Assessment (FO-P6-001) ───────────────────────────────

class TrainingNeedsCreate(BaseModel):
    code: str
    employee_name: str
    role: str
    skills_gap: str
    priority: str = "medium"
    status: str = "identified"


class TrainingNeedsUpdate(BaseModel):
    employee_name: Optional[str] = None
    role: Optional[str] = None
    skills_gap: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class TrainingNeedsResponse(BaseModel):
    id: int
    code: str
    employee_name: str
    role: str
    skills_gap: str
    priority: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Competency Matrix (MAT-P6-001) ──────────────────────────────────────

class CompetencyMatrixCreate(BaseModel):
    code: str
    role: str
    competencies: List[Dict[str, Any]] = Field(default_factory=list)
    version: str = "1.0"
    is_active: bool = True


class CompetencyMatrixUpdate(BaseModel):
    role: Optional[str] = None
    competencies: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None


class CompetencyMatrixResponse(BaseModel):
    id: int
    code: str
    role: str
    competencies: List[Dict[str, Any]]
    version: str
    is_active: bool

    model_config = {"from_attributes": True}


# ─── Course (SOP-P6-002) ─────────────────────────────────────────────────

class CourseCreate(BaseModel):
    code: str
    title: str
    modality: str
    duration_hours: int
    content: str
    status: str = "draft"


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    modality: Optional[str] = None
    duration_hours: Optional[int] = None
    content: Optional[str] = None
    status: Optional[str] = None


class CourseResponse(BaseModel):
    id: int
    code: str
    title: str
    modality: str
    duration_hours: int
    content: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Training Plan (PLN-P6-001) ──────────────────────────────────────────

class TrainingPlanCreate(BaseModel):
    code: str
    year: int
    courses: List[Any] = Field(default_factory=list)
    budget: float = 0.0
    status: str = "draft"


class TrainingPlanUpdate(BaseModel):
    courses: Optional[List[Any]] = None
    budget: Optional[float] = None
    status: Optional[str] = None


class TrainingPlanResponse(BaseModel):
    id: int
    code: str
    year: int
    courses: List[Any]
    budget: float
    status: str

    model_config = {"from_attributes": True}


# ─── Training Session (SOP-P6-003) ───────────────────────────────────────

class TrainingSessionCreate(BaseModel):
    course_id: int
    instructor: str
    start_date: date
    end_date: date
    attendees: List[str] = Field(default_factory=list)
    status: str = "scheduled"


class TrainingSessionUpdate(BaseModel):
    instructor: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    attendees: Optional[List[str]] = None
    status: Optional[str] = None


class TrainingSessionResponse(BaseModel):
    id: int
    course_id: int
    instructor: str
    start_date: date
    end_date: date
    attendees: List[str]
    status: str

    model_config = {"from_attributes": True}


# ─── Training Evaluation (FO-P6-002) ─────────────────────────────────────

class TrainingEvaluationCreate(BaseModel):
    session_id: int
    participant: str
    score: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class TrainingEvaluationUpdate(BaseModel):
    score: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None


class TrainingEvaluationResponse(BaseModel):
    id: int
    session_id: int
    participant: str
    score: int
    feedback: Optional[str]
    submitted_at: datetime

    model_config = {"from_attributes": True}


# ─── Attendance Record (REG-P6-001) ──────────────────────────────────────

class AttendanceRecordCreate(BaseModel):
    session_id: int
    participant_name: str
    hours_attended: float = 0.0


class AttendanceRecordUpdate(BaseModel):
    hours_attended: Optional[float] = None


class AttendanceRecordResponse(BaseModel):
    id: int
    session_id: int
    participant_name: str
    hours_attended: float
    signed_at: datetime

    model_config = {"from_attributes": True}


# ─── Certification Record (REG-P6-002) ───────────────────────────────────

class CertificationRecordCreate(BaseModel):
    code: str
    participant_name: str
    course_id: int
    certificate_code: str
    expires_at: Optional[date] = None
    status: str = "active"


class CertificationRecordUpdate(BaseModel):
    status: Optional[str] = None
    expires_at: Optional[date] = None


class CertificationRecordResponse(BaseModel):
    id: int
    code: str
    participant_name: str
    course_id: int
    certificate_code: str
    issued_at: datetime
    expires_at: Optional[date]
    status: str

    model_config = {"from_attributes": True}


# ─── User Manual (MAN-P6-001) ────────────────────────────────────────────

class UserManualCreate(BaseModel):
    code: str
    title: str
    product: str
    version: str = "1.0"
    content_url: str
    status: str = "draft"


class UserManualUpdate(BaseModel):
    title: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    content_url: Optional[str] = None
    status: Optional[str] = None


class UserManualResponse(BaseModel):
    id: int
    code: str
    title: str
    product: str
    version: str
    content_url: str
    status: str

    model_config = {"from_attributes": True}


# ─── Video Tutorial (GUIA-P6-001) ────────────────────────────────────────

class VideoTutorialCreate(BaseModel):
    code: str
    title: str
    course_id: Optional[int] = None
    url: str
    duration_minutes: int
    status: str = "draft"


class VideoTutorialUpdate(BaseModel):
    title: Optional[str] = None
    course_id: Optional[int] = None
    url: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None


class VideoTutorialResponse(BaseModel):
    id: int
    code: str
    title: str
    course_id: Optional[int]
    url: str
    duration_minutes: int
    status: str

    model_config = {"from_attributes": True}


# ─── Business Logic DTOs ─────────────────────────────────────────────────

class TrainingEffectivenessResponse(BaseModel):
    course_id: int
    avg_score: float
    completion_rate: float
    total_sessions: int
    completed_sessions: int
    total_attendees: int
