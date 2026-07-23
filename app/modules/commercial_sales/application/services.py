from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commercial_sales.domain.models import (
    Contract,
    ContractStatus,
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
from app.modules.commercial_sales.infrastructure.repositories import (
    contract_repo,
    lead_repo,
    onboarding_repo,
    proposal_repo,
    subscription_repo,
)


class CommercialService:
    @staticmethod
    async def qualify_lead(db: AsyncSession, lead_id: int, icp_score: int) -> Optional[Lead]:
        lead = await lead_repo.get_by_id(db, lead_id)
        if lead is None:
            return None
        lead.icp_match_score = icp_score
        lead.status = LeadStatus.QUALIFIED if icp_score >= 50 else LeadStatus.DISQUALIFIED
        await db.flush()
        return lead

    @staticmethod
    async def win_lead(db: AsyncSession, lead_id: int, proposal_id: int) -> Optional[Lead]:
        lead = await lead_repo.get_by_id(db, lead_id)
        if lead is None:
            return None

        proposal = await proposal_repo.get_by_id(db, proposal_id)
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
        contract_repo.add(db, contract)
        await db.flush()
        return lead

    @staticmethod
    async def activate_subscription(db: AsyncSession, contract_id: int, tier: str, seats: int = 1) -> Optional[SaasSubscription]:
        contract = await contract_repo.get_by_id(db, contract_id)
        if contract is None or contract.contract_type != ContractType.SUBSCRIPTION:
            return None

        sub = SaasSubscription(
            contract_id=contract_id,
            tier=tier,
            seats=seats,
            activated_at=datetime.now(timezone.utc),
        )
        subscription_repo.add(db, sub)
        await db.flush()
        return sub

    @staticmethod
    async def churn_subscription(db: AsyncSession, subscription_id: int, reason: str) -> Optional[SaasSubscription]:
        sub = await subscription_repo.get_by_id(db, subscription_id)
        if sub is None:
            return None
        sub.status = SubscriptionStatus.CHURNED
        sub.churned_at = datetime.now(timezone.utc)
        sub.churn_reason = reason
        await db.flush()
        return sub

    @staticmethod
    async def start_onboarding(db: AsyncSession, contract_id: int, steps: list[dict]) -> Optional[Onboarding]:
        onboarding = Onboarding(
            contract_id=contract_id,
            steps=steps,
            status=OnboardingStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
        )
        onboarding_repo.add(db, onboarding)
        await db.flush()
        return onboarding

    @staticmethod
    async def complete_onboarding_step(
        db: AsyncSession, onboarding_id: int, step_index: int
    ) -> Optional[Onboarding]:
        onboarding = await onboarding_repo.get_by_id(db, onboarding_id)
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

    @staticmethod
    async def accept_proposal(db: AsyncSession, proposal_id: int) -> Optional[Proposal]:
        proposal = await proposal_repo.get_by_id(db, proposal_id)
        if proposal is None:
            return None
        proposal.status = ProposalStatus.ACCEPTED
        proposal.accepted_at = datetime.now(timezone.utc)
        await db.flush()
        return proposal

    @staticmethod
    async def terminate_service_contract(
        db: AsyncSession, contract_id: int, reason: str
    ) -> Optional[Contract]:
        contract = await contract_repo.get_by_id(db, contract_id)
        if contract is None or contract.contract_type != ContractType.SOW:
            return None
        contract.status = ContractStatus.TERMINATED
        contract.churned_at = datetime.now(timezone.utc)
        contract.churn_reason = reason
        await db.flush()
        return contract

commercial_service = CommercialService()
