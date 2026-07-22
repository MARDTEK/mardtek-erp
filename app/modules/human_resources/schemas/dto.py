from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── JobDescription (PER-P7-001) ──────────────────────────────────────────

class JobDescriptionCreate(BaseModel):
    code: str
    title: str
    department: str
    reports_to: Optional[str] = None
    responsibilities: str
    requirements: str
    competencies: List[Dict[str, Any]] = []
    is_active: bool = True


class JobDescriptionUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    reports_to: Optional[str] = None
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    competencies: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class JobDescriptionResponse(BaseModel):
    id: int
    code: str
    title: str
    department: str
    reports_to: Optional[str]
    responsibilities: str
    requirements: str
    competencies: list
    is_active: bool

    model_config = {"from_attributes": True}


# ─── PersonnelRequest (FO-P7-001) ─────────────────────────────────────────

class PersonnelRequestCreate(BaseModel):
    code: str
    requested_by: str
    job_title: str
    department: str
    justification: str
    budget: Decimal = Field(..., decimal_places=2)


class PersonnelRequestUpdate(BaseModel):
    requested_by: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    justification: Optional[str] = None
    budget: Optional[Decimal] = None
    status: Optional[str] = None


class PersonnelRequestResponse(BaseModel):
    id: int
    code: str
    requested_by: str
    job_title: str
    department: str
    justification: str
    budget: Decimal
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── InductionChecklist (FO-P7-002) ───────────────────────────────────────

class InductionItem(BaseModel):
    item: str
    completed_at: Optional[datetime] = None
    verified_by: Optional[str] = None


class InductionChecklistCreate(BaseModel):
    employee_name: str
    hire_date: date
    items: List[InductionItem] = []


class InductionChecklistUpdate(BaseModel):
    employee_name: Optional[str] = None
    hire_date: Optional[date] = None
    items: Optional[List[InductionItem]] = None
    status: Optional[str] = None


class InductionChecklistResponse(BaseModel):
    id: int
    employee_name: str
    hire_date: date
    items: list
    status: str

    model_config = {"from_attributes": True}


# ─── IndividualDevelopmentPlan (REG-P7-002) ───────────────────────────────

class IDPGoal(BaseModel):
    goal: str
    target_date: Optional[date] = None
    status: str = "pending"


class IDPCourse(BaseModel):
    course: str
    provider: Optional[str] = None
    completed: bool = False


class IndividualDevelopmentPlanCreate(BaseModel):
    employee_name: str
    goals: List[IDPGoal] = []
    courses: List[IDPCourse] = []
    review_date: Optional[date] = None
    status: str = "active"


class IndividualDevelopmentPlanUpdate(BaseModel):
    employee_name: Optional[str] = None
    goals: Optional[List[IDPGoal]] = None
    courses: Optional[List[IDPCourse]] = None
    review_date: Optional[date] = None
    status: Optional[str] = None


class IndividualDevelopmentPlanResponse(BaseModel):
    id: int
    employee_name: str
    goals: list
    courses: list
    review_date: Optional[date]
    status: str

    model_config = {"from_attributes": True}


# ─── PerformanceEvaluation (FO-P7-003) ────────────────────────────────────

class PerformanceEvaluationCreate(BaseModel):
    employee_name: str
    evaluator: str
    period: str
    score: Optional[int] = Field(default=None, ge=1, le=5)
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    status: str = "draft"


class PerformanceEvaluationUpdate(BaseModel):
    employee_name: Optional[str] = None
    evaluator: Optional[str] = None
    period: Optional[str] = None
    score: Optional[int] = Field(default=None, ge=1, le=5)
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    status: Optional[str] = None


class PerformanceEvaluationResponse(BaseModel):
    id: int
    employee_name: str
    evaluator: str
    period: str
    score: Optional[int]
    strengths: Optional[str]
    improvements: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── LaborIncident (FO-P7-004) ────────────────────────────────────────────

class LaborIncidentCreate(BaseModel):
    code: str
    employee_name: str
    incident_type: str = Field(..., pattern=r"^(warning|accident|violation|grievance)$")
    description: str
    resolution: Optional[str] = None
    status: str = "open"


class LaborIncidentUpdate(BaseModel):
    employee_name: Optional[str] = None
    incident_type: Optional[str] = None
    description: Optional[str] = None
    resolution: Optional[str] = None
    status: Optional[str] = None


class LaborIncidentResponse(BaseModel):
    id: int
    code: str
    employee_name: str
    incident_type: str
    description: str
    resolution: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── State Transition Schemas ─────────────────────────────────────────────

class PersonnelRequestTransition(BaseModel):
    target_status: str


class PerformanceEvaluationTransition(BaseModel):
    target_status: str


# ─── CompetencyAssessment ──────────────────────────────────────────────────

class CompetencyAssessmentCreate(BaseModel):
    employee_id: int
    skill: str
    assessed_level: str
    required_level: str
    has_gap: bool = True


class CompetencyAssessmentResponse(BaseModel):
    id: int
    employee_id: int
    skill: str
    assessed_level: str
    required_level: str
    has_gap: bool
    assessed_at: datetime

    model_config = {"from_attributes": True}


# ─── StaffRegister (REG-P7-001) ───────────────────────────────────────────

class StaffRegisterCreate(BaseModel):
    employee_name: str
    email: str
    department: str
    position: str
    hire_date: date
    contract_type: str = Field(..., pattern=r"^(permanent|contractor|intern)$")
    status: str = "active"


class StaffRegisterUpdate(BaseModel):
    employee_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    contract_type: Optional[str] = None
    status: Optional[str] = None


class StaffRegisterResponse(BaseModel):
    id: int
    employee_name: str
    email: str
    department: str
    position: str
    hire_date: date
    contract_type: str
    status: str

    model_config = {"from_attributes": True}
