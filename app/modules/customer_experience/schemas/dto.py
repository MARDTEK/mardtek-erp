from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── NpsSurvey ───────────────────────────────────────────────────────────

class NpsSurveyCreate(BaseModel):
    code: str
    customer_email: str
    subscription_id: Optional[int] = None
    score: int = Field(..., ge=0, le=10)
    feedback: Optional[str] = None


class NpsSurveyResponse(BaseModel):
    id: int
    code: str
    customer_email: str
    subscription_id: Optional[int]
    score: int
    category: str
    feedback: Optional[str]
    responded_at: datetime

    model_config = {"from_attributes": True}


# ─── CsatSurvey ──────────────────────────────────────────────────────────

class CsatSurveyCreate(BaseModel):
    code: str
    customer_email: str
    project_id: Optional[int] = None
    score: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class CsatSurveyResponse(BaseModel):
    id: int
    code: str
    customer_email: str
    project_id: Optional[int]
    score: int
    feedback: Optional[str]
    responded_at: datetime

    model_config = {"from_attributes": True}


# ─── CesSurvey ───────────────────────────────────────────────────────────

class CesSurveyCreate(BaseModel):
    code: str
    customer_email: str
    subscription_id: Optional[int] = None
    score: int = Field(..., ge=1, le=7)
    task_description: str


class CesSurveyResponse(BaseModel):
    id: int
    code: str
    customer_email: str
    subscription_id: Optional[int]
    score: int
    task_description: str
    responded_at: datetime

    model_config = {"from_attributes": True}


# ─── ComplaintClaim ──────────────────────────────────────────────────────

class ComplaintClaimCreate(BaseModel):
    code: str
    customer_email: str
    contract_id: Optional[int] = None
    type: str  # complaint | claim
    description: str
    desired_outcome: Optional[str] = None
    escalation_level: int = Field(1, ge=1, le=3)
    nc_id: Optional[int] = None


class ComplaintClaimUpdate(BaseModel):
    status: Optional[str] = None
    escalation_level: Optional[int] = Field(None, ge=1, le=3)
    desired_outcome: Optional[str] = None
    nc_id: Optional[int] = None


class ComplaintClaimResponse(BaseModel):
    id: int
    code: str
    customer_email: str
    contract_id: Optional[int]
    type: str
    description: str
    desired_outcome: Optional[str]
    status: str
    resolved_at: Optional[datetime]
    escalation_level: int
    nc_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── ComplaintRegister ───────────────────────────────────────────────────

class ComplaintRegisterCreate(BaseModel):
    complaint_id: int
    category: str
    resolution_days: Optional[int] = None


class ComplaintRegisterResponse(BaseModel):
    id: int
    complaint_id: int
    registered_at: datetime
    category: str
    resolution_days: Optional[int]

    model_config = {"from_attributes": True}


# ─── ExitInterview ───────────────────────────────────────────────────────

class ExitInterviewCreate(BaseModel):
    code: str
    subscription_id: int
    churn_reason_category: str
    detailed_feedback: Optional[str] = None
    would_return: Optional[bool] = None


class ExitInterviewResponse(BaseModel):
    id: int
    code: str
    subscription_id: int
    churn_reason_category: str
    detailed_feedback: Optional[str]
    would_return: Optional[bool]
    interview_date: datetime

    model_config = {"from_attributes": True}


# ─── SatisfactionReport ──────────────────────────────────────────────────

class SatisfactionReportCreate(BaseModel):
    code: str
    period: str
    nps_score: Optional[float] = None
    csat_score: Optional[float] = None
    ces_score: Optional[float] = None
    complaints_count: Optional[int] = None
    response_rate: Optional[float] = None
    recommendations: Optional[str] = None


class SatisfactionReportResponse(BaseModel):
    id: int
    code: str
    period: str
    nps_score: Optional[float]
    csat_score: Optional[float]
    ces_score: Optional[float]
    complaints_count: Optional[int]
    response_rate: Optional[float]
    recommendations: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
