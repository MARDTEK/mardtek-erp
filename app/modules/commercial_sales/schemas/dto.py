from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.modules.commercial_sales.domain.models import (
    ContractStatus,
    ProposalStatus,
)


# ─── Lead ────────────────────────────────────────────────────────────────

class LeadCreate(BaseModel):
    company: str
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    source: str
    product_line: str = Field(..., pattern=r"^(SERVICIOS|SAAS)$")
    estimated_value: Optional[Decimal] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    company: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    estimated_value: Optional[Decimal] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    company: str
    contact_name: str
    contact_email: str
    contact_phone: Optional[str]
    source: str
    icp_match_score: Optional[int]
    status: str
    product_line: str
    estimated_value: Optional[Decimal]
    assigned_to: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadQualify(BaseModel):
    icp_score: int = Field(..., ge=0, le=100)


# ─── Discovery ───────────────────────────────────────────────────────────

class DiscoveryCreate(BaseModel):
    needs: str
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    decision_criteria: Optional[str] = None
    pain_points: Optional[str] = None
    recorded_by: str


class DiscoveryResponse(BaseModel):
    id: int
    lead_id: int
    needs: str
    budget_range: Optional[str]
    timeline: Optional[str]
    decision_criteria: Optional[str]
    pain_points: Optional[str]
    recorded_by: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


# ─── Proposal ────────────────────────────────────────────────────────────

class ProposalLine(BaseModel):
    description: str
    quantity: int = 1
    unit_price: Decimal
    total: Decimal


class ProposalCreate(BaseModel):
    total_amount: Decimal
    lines: List[Dict[str, Any]] = []
    valid_until: Optional[date] = None
    created_by: str


class ProposalResponse(BaseModel):
    id: int
    lead_id: int
    version: str
    total_amount: Decimal
    lines: list
    status: ProposalStatus
    valid_until: Optional[date]
    sent_at: Optional[datetime]
    accepted_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Contract ────────────────────────────────────────────────────────────

class ContractResponse(BaseModel):
    id: int
    lead_id: int
    proposal_id: Optional[int]
    contract_type: str
    contract_number: str
    signed_at: datetime
    start_date: date
    end_date: Optional[date]
    total_value: Decimal
    monthly_value: Optional[Decimal]
    sla_clauses: Optional[str]
    status: ContractStatus
    churned_at: Optional[datetime] = None
    churn_reason: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── SaaS Subscription ───────────────────────────────────────────────────

class SubscriptionActivate(BaseModel):
    tier: str = Field(..., pattern=r"^(basic|professional|enterprise)$")
    seats: int = Field(default=1, ge=1)


class SubscriptionChurn(BaseModel):
    reason: str


class SubscriptionResponse(BaseModel):
    id: int
    contract_id: int
    product: str
    tier: str
    status: str
    seats: int
    activated_at: Optional[datetime]
    churned_at: Optional[datetime]
    churn_reason: Optional[str]

    model_config = {"from_attributes": True}


# ─── Onboarding ──────────────────────────────────────────────────────────

class OnboardingStart(BaseModel):
    steps: List[Dict[str, Any]] = []


class OnboardingResponse(BaseModel):
    id: int
    contract_id: int
    steps: list
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── Account Plan ────────────────────────────────────────────────────────

class AccountPlanCreate(BaseModel):
    goals: str
    activities: List[Dict[str, Any]] = []
    review_date: Optional[date] = None
    notes: Optional[str] = None


class AccountPlanResponse(BaseModel):
    id: int
    contract_id: int
    goals: str
    activities: list
    review_date: Optional[date]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Retention Action ────────────────────────────────────────────────────

class RetentionActionCreate(BaseModel):
    action_type: str
    description: str
    assigned_to: str
    deadline: Optional[date] = None


class RetentionActionResponse(BaseModel):
    id: int
    subscription_id: int
    action_type: str
    description: str
    status: str
    assigned_to: str
    deadline: Optional[date]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── ICP Matrix ──────────────────────────────────────────────────────────

class IcpMatrixCreate(BaseModel):
    industry: str
    company_size: str
    role: str
    pain_points: str
    fit_score: int = Field(default=50, ge=0, le=100)


class IcpMatrixResponse(BaseModel):
    id: int
    industry: str
    company_size: str
    role: str
    pain_points: str
    fit_score: int
    is_active: bool

    model_config = {"from_attributes": True}


# ─── Quote (SOP-P3-004) ────────────────────────────────────────────────

class QuoteCreate(BaseModel):
    subtotal: Decimal
    tax_rate: Decimal = Decimal("0.00")
    discount_percent: Decimal = Decimal("0.00")
    total: Decimal
    lines: List[Dict[str, Any]] = []
    currency: str = "USD"
    valid_until: Optional[date] = None
    notes: Optional[str] = None
    created_by: str


class QuoteResponse(BaseModel):
    id: int
    lead_id: int
    quote_number: str
    version: str
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    total: Decimal
    lines: list
    currency: str
    valid_until: Optional[date]
    notes: Optional[str]
    status: str
    sent_at: Optional[datetime]
    accepted_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Project Handoff (SOP-P3-006) ──────────────────────────────────────

class ProjectHandoffCreate(BaseModel):
    target_module: str = Field(..., pattern=r"^(P4|P5)$")
    project_manager: str
    handoff_notes: Optional[str] = None
    checklist: List[Dict[str, Any]] = []


class ProjectHandoffResponse(BaseModel):
    id: int
    contract_id: int
    target_module: str
    project_manager: str
    handoff_notes: Optional[str]
    checklist: list
    status: str
    signed_by_sales: Optional[str]
    signed_by_pm: Optional[str]
    signed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Churn Analysis (SOP-P3-009) ───────────────────────────────────────

class ChurnAnalysisCreate(BaseModel):
    analysis_date: date
    root_cause: str
    category: str = Field(..., pattern=r"^(price|product_fit|support|performance|competitor|other)$")
    revenue_lost: Decimal
    lifetime_value: Optional[Decimal] = None
    retention_attempts: List[Dict[str, Any]] = []
    recommendations: Optional[str] = None
    analyzed_by: str


class ChurnAnalysisResponse(BaseModel):
    id: int
    subscription_id: int
    analysis_date: date
    root_cause: str
    category: str
    revenue_lost: Decimal
    lifetime_value: Optional[Decimal]
    retention_attempts: list
    recommendations: Optional[str]
    analyzed_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Service Contract Churn (SERVICIOS) ─────────────────────────────────

class ServiceChurnTerminate(BaseModel):
    reason: str


class ServiceChurnAnalysisCreate(BaseModel):
    analysis_date: date
    root_cause: str
    category: str = Field(..., pattern=r"^(scope_creep|budget_overrun|timeline_issues|quality_concerns|relationship_breakdown|strategic_shift|other)$")
    revenue_lost: Decimal
    delivery_completion_pct: Optional[int] = Field(None, ge=0, le=100)
    retention_attempts: List[Dict[str, Any]] = []
    recommendations: Optional[str] = None
    analyzed_by: str


class ServiceChurnAnalysisResponse(BaseModel):
    id: int
    contract_id: int
    analysis_date: date
    root_cause: str
    category: str
    revenue_lost: Decimal
    delivery_completion_pct: Optional[int]
    retention_attempts: list
    recommendations: Optional[str]
    analyzed_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Marketing Plan (PLN-P3-001) ──────────────────────────────────────

class MarketingPlanCreate(BaseModel):
    icp_matrix_id: Optional[int] = None
    name: str
    objectives: str
    target_segments: List[Dict[str, Any]] = []
    budget: Optional[Decimal] = None
    channels: List[str] = []
    kpis: List[Dict[str, Any]] = []
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_by: str


class MarketingPlanResponse(BaseModel):
    id: int
    icp_matrix_id: Optional[int]
    name: str
    objectives: str
    target_segments: list
    budget: Optional[Decimal]
    channels: list
    kpis: list
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Competition Matrix (MAT-P3-002) ───────────────────────────────────

class CompetitionMatrixCreate(BaseModel):
    icp_matrix_id: Optional[int] = None
    competitor_name: str
    product_category: str
    strengths: str
    weaknesses: str
    pricing_model: Optional[str] = None
    estimated_market_share: Optional[int] = Field(None, ge=0, le=100)
    threat_level: Optional[str] = Field(None, pattern=r"^(low|medium|high)$")
    notes: Optional[str] = None


class CompetitionMatrixResponse(BaseModel):
    id: int
    icp_matrix_id: Optional[int]
    competitor_name: str
    product_category: str
    strengths: str
    weaknesses: str
    pricing_model: Optional[str]
    estimated_market_share: Optional[int]
    threat_level: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
