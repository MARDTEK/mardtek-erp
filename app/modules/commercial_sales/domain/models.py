from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────

class LeadStatus(str, enum.Enum):
    NEW = "new"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    DISQUALIFIED = "disqualified"


class ContractType(str, enum.Enum):
    SOW = "sow"           # Statement of Work (SERVICIOS)
    SUBSCRIPTION = "subscription"  # SaaS


class SubscriptionTier(str, enum.Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    CHURNED = "churned"


class OnboardingStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ProposalStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    NEGOTIATION = "negotiation"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ContractStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    TERMINATED = "terminated"


# ─── Models ──────────────────────────────────────────────────────────────

class Lead(Base):
    """FO-P3-001 | Lead Qualification — tracks prospects through the pipeline."""

    __tablename__ = "commercial_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50))

    source: Mapped[str] = mapped_column(String(100), nullable=False)  # website, referral, inbound, event, etc.
    icp_match_score: Mapped[Optional[int]] = mapped_column(Integer)  # 0–100
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.NEW)

    product_line: Mapped[str] = mapped_column(String(20), nullable=False)  # SERVICIOS or SAAS
    estimated_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    assigned_to: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    discovery: Mapped[Optional["Discovery"]] = relationship(back_populates="lead", uselist=False)
    proposals: Mapped[List["Proposal"]] = relationship(back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Lead {self.company} [{self.status.value}]>"


class Discovery(Base):
    """FO-P3-002 | Discovery Questionnaire — needs analysis for a lead."""

    __tablename__ = "commercial_discoveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commercial_leads.id"), unique=True, nullable=False
    )

    needs: Mapped[str] = mapped_column(Text, nullable=False)
    budget_range: Mapped[Optional[str]] = mapped_column(String(255))
    timeline: Mapped[Optional[str]] = mapped_column(String(255))
    decision_criteria: Mapped[Optional[str]] = mapped_column(Text)
    pain_points: Mapped[Optional[str]] = mapped_column(Text)

    recorded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    lead: Mapped[Lead] = relationship(back_populates="discovery")

    def __repr__(self) -> str:
        return f"<Discovery for Lead #{self.lead_id}>"


class Proposal(Base):
    """SOP-P3-003 | Technical Proposal — commercial offer sent to a lead."""

    __tablename__ = "commercial_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commercial_leads.id"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(10), default="1.0")

    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    lines: Mapped[dict] = mapped_column(JSON, default=list)  # List of {description, qty, unit_price, total}

    status: Mapped[ProposalStatus] = mapped_column(Enum(ProposalStatus), default=ProposalStatus.DRAFT)
    valid_until: Mapped[Optional[date]] = mapped_column(Date)

    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    lead: Mapped[Lead] = relationship(back_populates="proposals")

    def __repr__(self) -> str:
        return f"<Proposal #{self.id} v{self.version} ${self.total_amount} [{self.status}]>"


class Contract(Base):
    """SOP-P3-005 | Contract — SOW for services, subscription for SaaS."""

    __tablename__ = "commercial_contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commercial_leads.id"), nullable=False
    )
    proposal_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("commercial_proposals.id")
    )

    contract_type: Mapped[ContractType] = mapped_column(Enum(ContractType), nullable=False)
    contract_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    total_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    monthly_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    sla_clauses: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.ACTIVE)

    # Relationships
    subscription: Mapped[Optional["SaasSubscription"]] = relationship(back_populates="contract", uselist=False)
    onboarding: Mapped[Optional["Onboarding"]] = relationship(back_populates="contract", uselist=False)

    def __repr__(self) -> str:
        return f"<Contract {self.contract_number} [{self.contract_type.value}] {self.status}>"


class SaasSubscription(Base):
    """SOP-P3-009 | SaaS Subscription — MicroSmart subscription tracking."""

    __tablename__ = "commercial_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commercial_contracts.id"), unique=True, nullable=False
    )

    product: Mapped[str] = mapped_column(String(100), default="MicroSmart")
    tier: Mapped[SubscriptionTier] = mapped_column(Enum(SubscriptionTier), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE
    )

    seats: Mapped[int] = mapped_column(Integer, default=1)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    churned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    churn_reason: Mapped[Optional[str]] = mapped_column(Text)

    contract: Mapped[Contract] = relationship(back_populates="subscription")

    def __repr__(self) -> str:
        return f"<SaasSubscription {self.product} {self.tier.value} [{self.status.value}]>"


class Onboarding(Base):
    """SOP-P3-007 | Customer Activation and Onboarding."""

    __tablename__ = "commercial_onboarding"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commercial_contracts.id"), unique=True, nullable=False
    )

    steps: Mapped[dict] = mapped_column(JSON, default=list)  # [{step, completed_at, assigned_to}]
    status: Mapped[OnboardingStatus] = mapped_column(
        Enum(OnboardingStatus), default=OnboardingStatus.PENDING
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    contract: Mapped[Contract] = relationship(back_populates="onboarding")

    def __repr__(self) -> str:
        return f"<Onboarding for Contract #{self.contract_id} [{self.status.value}]>"


class AccountPlan(Base):
    """PLN-P3-002 | Account Plan — strategic account management."""

    __tablename__ = "commercial_account_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commercial_contracts.id"), nullable=False
    )

    goals: Mapped[str] = mapped_column(Text, nullable=False)
    activities: Mapped[dict] = mapped_column(JSON, default=list)
    review_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<AccountPlan for Contract #{self.contract_id}>"


class RetentionAction(Base):
    """SOP-P3-008 | Retention Plan Management — actions to prevent churn."""

    __tablename__ = "commercial_retention_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commercial_subscriptions.id"), nullable=False
    )

    action_type: Mapped[str] = mapped_column(String(100), nullable=False)  # discount, training, support, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="planned")  # planned, in_progress, completed

    assigned_to: Mapped[str] = mapped_column(String(255), nullable=False)
    deadline: Mapped[Optional[date]] = mapped_column(Date)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<RetentionAction {self.action_type} [{self.status}]>"


class IcpMatrix(Base):
    """MAT-P3-001 | ICP and Buyer Persona Matrix — ideal customer profile."""

    __tablename__ = "commercial_icp_matrix"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    company_size: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)

    pain_points: Mapped[str] = mapped_column(Text, nullable=False)
    fit_score: Mapped[int] = mapped_column(Integer, default=50)  # 0–100
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<IcpMatrix {self.industry} — {self.role}>"
