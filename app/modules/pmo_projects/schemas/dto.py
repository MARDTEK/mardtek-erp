from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Project ─────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    code: str
    name: str
    contract_id: Optional[int] = None
    description: Optional[str] = None
    product_line: str = Field(..., pattern=r"^(SERVICIOS|SAAS)$")
    status: str = "kicked_off"
    start_date: date
    end_date: Optional[date] = None
    budget: Optional[Decimal] = None
    project_manager: str


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = None
    project_manager: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    code: str
    name: str
    contract_id: Optional[int]
    description: Optional[str]
    product_line: str
    status: str
    start_date: date
    end_date: Optional[date]
    budget: Optional[Decimal]
    project_manager: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Project Execution Plan ──────────────────────────────────────────────

class ExecutionPlanCreate(BaseModel):
    phases: List[Dict[str, Any]] = []
    milestones: List[Dict[str, Any]] = []
    risks: List[Dict[str, Any]] = []
    status: str = "draft"


class ExecutionPlanUpdate(BaseModel):
    phases: Optional[List[Dict[str, Any]]] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    risks: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class ExecutionPlanResponse(BaseModel):
    id: int
    project_id: int
    phases: list
    milestones: list
    risks: list
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Change Request ──────────────────────────────────────────────────────

class ChangeRequestCreate(BaseModel):
    code: str
    description: str
    reason: str
    impact_analysis: Optional[str] = None
    requested_by: str


class ChangeRequestUpdate(BaseModel):
    description: Optional[str] = None
    reason: Optional[str] = None
    impact_analysis: Optional[str] = None
    status: Optional[str] = None
    approved_by: Optional[str] = None


class ChangeRequestResponse(BaseModel):
    id: int
    project_id: int
    code: str
    description: str
    reason: str
    impact_analysis: Optional[str]
    status: str
    requested_by: str
    approved_by: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeRequestApprove(BaseModel):
    approved_by: str


# ─── Weekly Progress Report ──────────────────────────────────────────────

class WeeklyReportCreate(BaseModel):
    week_number: int = Field(..., ge=1, le=53)
    year: int = Field(..., ge=2000, le=2100)
    accomplishments: str
    next_week_plan: str
    blockers: Optional[str] = None
    status_percent: int = Field(default=0, ge=0, le=100)


class WeeklyReportUpdate(BaseModel):
    accomplishments: Optional[str] = None
    next_week_plan: Optional[str] = None
    blockers: Optional[str] = None
    status_percent: Optional[int] = Field(None, ge=0, le=100)


class WeeklyReportResponse(BaseModel):
    id: int
    project_id: int
    week_number: int
    year: int
    accomplishments: str
    next_week_plan: str
    blockers: Optional[str]
    status_percent: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Deliverables Checklist ──────────────────────────────────────────────

class DeliverableItem(BaseModel):
    name: str
    description: str
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    verified_by: Optional[str] = None


class DeliverablesChecklistCreate(BaseModel):
    items: List[DeliverableItem] = []


class DeliverablesChecklistUpdate(BaseModel):
    items: Optional[List[DeliverableItem]] = None
    status: Optional[str] = None


class DeliverablesChecklistResponse(BaseModel):
    id: int
    project_id: int
    items: list
    status: str

    model_config = {"from_attributes": True}


# ─── Follow-Up Meeting ───────────────────────────────────────────────────

class FollowUpMeetingCreate(BaseModel):
    date: date
    minutes: str
    action_items: List[Dict[str, Any]] = []
    next_meeting_date: Optional[date] = None


class FollowUpMeetingUpdate(BaseModel):
    minutes: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    next_meeting_date: Optional[date] = None


class FollowUpMeetingResponse(BaseModel):
    id: int
    project_id: int
    date: date
    minutes: str
    action_items: list
    next_meeting_date: Optional[date]

    model_config = {"from_attributes": True}


# ─── Handover Acceptance ─────────────────────────────────────────────────

class HandoverAcceptanceCreate(BaseModel):
    accepted_by: str
    comments: Optional[str] = None
    warranty_period_days: int = 90


class HandoverAcceptanceResponse(BaseModel):
    id: int
    project_id: int
    accepted_by: str
    accepted_at: datetime
    comments: Optional[str]
    warranty_period_days: int
    status: str

    model_config = {"from_attributes": True}


class HandoverAcceptanceSign(BaseModel):
    status: str = "signed"


# ─── Project Closure ─────────────────────────────────────────────────────

class ProjectClosureCreate(BaseModel):
    lessons_learned: Optional[str] = None
    final_budget: Optional[Decimal] = None
    customer_feedback: Optional[str] = None


class ProjectClosureResponse(BaseModel):
    id: int
    project_id: int
    closed_at: datetime
    lessons_learned: Optional[str]
    final_budget: Optional[Decimal]
    customer_feedback: Optional[str]
    status: str

    model_config = {"from_attributes": True}


# ─── Progress ────────────────────────────────────────────────────────────

class ProgressResponse(BaseModel):
    total: int
    completed: int
    percentage: float
