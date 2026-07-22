from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ─── Document ────────────────────────────────────────────────────────────

class DocumentCreate(BaseModel):
    code: str = Field(..., pattern=r"^(SOP|FO|REG|PLN|POL|MAN|MAT|GUIA|INF|PL|PER|FIC|DO)-P\d{1,2}-\d{3}-.+")
    title: str
    process_code: str = Field(..., pattern=r"P(1[0-1]|[1-9])")
    doc_type: str = Field(..., pattern=r"^(SOP|FO|REG|PLN|POL|MAN|MAT|GUIA|INF|PL|PER|FIC|DO)$")
    file_path: Optional[str] = None
    next_review_at: Optional[date] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    file_path: Optional[str] = None
    next_review_at: Optional[date] = None


class DocumentResponse(BaseModel):
    id: int
    code: str
    title: str
    process_code: str
    doc_type: str
    version: str
    status: str
    file_path: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    next_review_at: Optional[date]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Non-Conformity ──────────────────────────────────────────────────────

class NCCreate(BaseModel):
    code: str = Field(..., pattern=r"^NC-\d{4}-\d{3,}$")
    source: str
    source_ref: Optional[str] = None
    description: str
    severity: str = Field(..., pattern=r"^(minor|major|critical)$")
    reported_by: str


class NCResponse(BaseModel):
    id: int
    code: str
    source: str
    source_ref: Optional[str]
    description: str
    severity: str
    root_cause: Optional[str]
    status: str
    reported_by: str
    reported_at: datetime
    closed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class NCUpdateRootCause(BaseModel):
    root_cause: str


class NCStateTransition(BaseModel):
    target_status: str = Field(..., pattern=r"^(investigating|corrective_action|closed)$")


# ─── Corrective Action ───────────────────────────────────────────────────

class CorrectiveActionCreate(BaseModel):
    code: str = Field(..., pattern=r"^CA-\d{4}-\d{3,}$")
    nc_id: int
    description: str
    responsible: str
    deadline: date


class CorrectiveActionResponse(BaseModel):
    id: int
    code: str
    nc_id: int
    description: str
    responsible: str
    deadline: date
    implementation_evidence: Optional[str]
    effectiveness_review: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class CorrectiveActionVerify(BaseModel):
    effectiveness_review: str


# ─── Internal Audit ──────────────────────────────────────────────────────

class AuditCreate(BaseModel):
    code: str
    scheduled_date: date
    scope: str
    auditor: str
    audited_process: str = Field(..., pattern=r"P(1[0-1]|[1-9])")


class AuditResponse(BaseModel):
    id: int
    code: str
    scheduled_date: date
    audit_date: Optional[date]
    scope: str
    auditor: str
    audited_process: str
    status: str
    result: Optional[str]
    findings_summary: Optional[str]
    report_url: Optional[str]

    model_config = {"from_attributes": True}


class ChecklistItemCreate(BaseModel):
    question: str


class ChecklistItemResponse(BaseModel):
    id: int
    audit_id: int
    question: str
    result: Optional[str]
    evidence: Optional[str]
    nc_id: Optional[int]

    model_config = {"from_attributes": True}


class ChecklistItemUpdate(BaseModel):
    result: str  # pass, fail, na
    evidence: Optional[str] = None
    nc_id: Optional[int] = None


# ─── Process Owner ───────────────────────────────────────────────────────

class ProcessOwnerCreate(BaseModel):
    process_code: str = Field(..., pattern=r"P(1[0-1]|[1-9])")
    process_name: str
    owner_name: str
    role: str
    since_date: date


class ProcessOwnerResponse(BaseModel):
    id: int
    process_code: str
    process_name: str
    owner_name: str
    role: str
    since_date: date
    is_active: bool

    model_config = {"from_attributes": True}


# ─── Continuous Improvement ──────────────────────────────────────────────

class ImprovementCreate(BaseModel):
    code: str
    source: str
    source_ref: Optional[str] = None
    description: str
    expected_benefit: Optional[str] = None
    responsible: str


class ImprovementResponse(BaseModel):
    id: int
    code: str
    source: str
    source_ref: Optional[str]
    description: str
    expected_benefit: Optional[str]
    responsible: str
    status: str
    created_at: datetime
    implemented_at: Optional[datetime]

    model_config = {"from_attributes": True}
