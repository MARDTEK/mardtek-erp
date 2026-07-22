"""Business logic for P3 — Commercial Prospecting & Management."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commercial_sales.domain.models import (
    Contract,
    ContractType,
    Lead,
    LeadStatus,
    Onboarding,
    OnboardingStatus,
    Proposal,
    ProposalStatus,
    SaasSubscription,
    SubscriptionStatus,
)


# ─── Pipeline Logic ──────────────────────────────────────────────────────

async def qualify_lead(db: AsyncSession, lead_id: int, icp_score: int) -> Optional[Lead]:
    """Mark a lead as qualified if ICP score meets threshold."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if lead is None:
        return None
    lead.icp_match_score = icp_score
    lead.status = LeadStatus.QUALIFIED if icp_score >= 50 else LeadStatus.DISQUALIFIED
    await db.flush()
    return lead


async def win_lead(db: AsyncSession, lead_id: int, proposal_id: int) -> Optional[Lead]:
    """Move lead to WON and create contract from accepted proposal."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if lead is None:
        return None

    proposal_result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = proposal_result.scalar_one_or_none()
    if proposal is None:
        return None

    lead.status = LeadStatus.WON
    proposal.status = ProposalStatus.ACCEPTED
    proposal.accepted_at = datetime.now(timezone.utc)

    # Auto-create contract
    contract = Contract(
        lead_id=lead_id,
        proposal_id=proposal_id,
        contract_type=ContractType.SOW if lead.product_line == "SERVICIOS" else ContractType.SUBSCRIPTION,
        contract_number=f"CTR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        signed_at=datetime.now(timezone.utc),
        start_date=date.today(),
        total_value=proposal.total_amount,
    )
    db.add(contract)
    await db.flush()
    return lead


# ─── SaaS Subscription Logic ─────────────────────────────────────────────

async def activate_subscription(db: AsyncSession, contract_id: int, tier: str, seats: int = 1) -> Optional[SaasSubscription]:
    """Activate a SaaS subscription after contract signing."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if contract is None or contract.contract_type != ContractType.SUBSCRIPTION:
        return None

    sub = SaasSubscription(
        contract_id=contract_id,
        tier=tier,
        seats=seats,
        activated_at=datetime.now(timezone.utc),
    )
    db.add(sub)
    await db.flush()
    return sub


async def churn_subscription(db: AsyncSession, subscription_id: int, reason: str) -> Optional[SaasSubscription]:
    """Mark a subscription as churned with reason."""
    result = await db.execute(
        select(SaasSubscription).where(SaasSubscription.id == subscription_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        return None
    sub.status = SubscriptionStatus.CHURNED
    sub.churned_at = datetime.now(timezone.utc)
    sub.churn_reason = reason
    await db.flush()
    return sub


# ─── Onboarding Logic ────────────────────────────────────────────────────

async def start_onboarding(db: AsyncSession, contract_id: int, steps: list[dict]) -> Optional[Onboarding]:
    """Create an onboarding plan for a won contract."""
    onboarding = Onboarding(
        contract_id=contract_id,
        steps=steps,
        status=OnboardingStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc),
    )
    db.add(onboarding)
    await db.flush()
    return onboarding


async def complete_onboarding_step(
    db: AsyncSession, onboarding_id: int, step_index: int
) -> Optional[Onboarding]:
    """Mark an onboarding step as completed."""
    result = await db.execute(select(Onboarding).where(Onboarding.id == onboarding_id))
    onboarding = result.scalar_one_or_none()
    if onboarding is None:
        return None

    steps = list(onboarding.steps)
    if step_index < 0 or step_index >= len(steps):
        return None

    steps[step_index]["completed_at"] = datetime.now(timezone.utc).isoformat()
    onboarding.steps = steps

    # Check if all steps are done
    if all(s.get("completed_at") for s in steps):
        onboarding.status = OnboardingStatus.COMPLETED
        onboarding.completed_at = datetime.now(timezone.utc)

    await db.flush()
    return onboarding


# ─── Proposal Logic ──────────────────────────────────────────────────────

async def accept_proposal(db: AsyncSession, proposal_id: int) -> Optional[Proposal]:
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    if proposal is None:
        return None
    proposal.status = ProposalStatus.ACCEPTED
    proposal.accepted_at = datetime.now(timezone.utc)
    await db.flush()
    return proposal
