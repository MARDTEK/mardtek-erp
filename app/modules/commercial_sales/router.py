from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.modules.commercial_sales.domain.logic import (
    accept_proposal,
    activate_subscription,
    churn_subscription,
    complete_onboarding_step,
    qualify_lead,
    start_onboarding,
    win_lead,
)
from app.modules.commercial_sales.domain.models import (
    AccountPlan,
    Contract,
    Discovery,
    IcpMatrix,
    Lead,
    Onboarding,
    Proposal,
    RetentionAction,
    SaasSubscription,
)
from app.modules.commercial_sales.schemas.dto import (
    AccountPlanCreate,
    AccountPlanResponse,
    ContractResponse,
    DiscoveryCreate,
    DiscoveryResponse,
    IcpMatrixCreate,
    IcpMatrixResponse,
    LeadCreate,
    LeadQualify,
    LeadResponse,
    LeadUpdate,
    OnboardingResponse,
    OnboardingStart,
    ProposalCreate,
    ProposalResponse,
    RetentionActionCreate,
    RetentionActionResponse,
    SubscriptionActivate,
    SubscriptionChurn,
    SubscriptionResponse,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# ─── Leads (CRM Pipeline) ────────────────────────────────────────────────

@router.get("/leads", response_model=List[LeadResponse])
async def list_leads(
    status: str | None = None,
    product_line: str | None = None,
    assigned_to: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Lead)
    if status:
        stmt = stmt.where(Lead.status == status)
    if product_line:
        stmt = stmt.where(Lead.product_line == product_line)
    if assigned_to:
        stmt = stmt.where(Lead.assigned_to == assigned_to)
    result = await db.execute(stmt.order_by(Lead.created_at.desc()))
    return list(result.scalars().all())


@router.post("/leads", response_model=LeadResponse, status_code=201)
async def create_lead(payload: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead = Lead(**payload.model_dump())
    db.add(lead)
    await db.flush()
    return lead


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: int, payload: LeadUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    await db.flush()
    return lead


@router.post("/leads/{lead_id}/qualify", response_model=LeadResponse)
async def qualify_lead_endpoint(lead_id: int, payload: LeadQualify, db: AsyncSession = Depends(get_db)):
    lead = await qualify_lead(db, lead_id, payload.icp_score)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/leads/{lead_id}/win", response_model=LeadResponse)
async def win_lead_endpoint(
    lead_id: int,
    proposal_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    lead = await win_lead(db, lead_id, proposal_id)
    if not lead:
        raise HTTPException(status_code=400, detail="Could not close lead as won. Check lead and proposal exist.")
    await event_bus.emit(Event(
        name="LeadWon",
        payload={"lead_id": lead_id, "proposal_id": proposal_id},
        source_module="commercial_sales",
    ))
    return lead


# ─── Discovery ───────────────────────────────────────────────────────────

@router.get("/leads/{lead_id}/discovery", response_model=DiscoveryResponse)
async def get_discovery(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Discovery).where(Discovery.lead_id == lead_id)
    )
    disc = result.scalar_one_or_none()
    if not disc:
        raise HTTPException(status_code=404, detail="Discovery not found for this lead")
    return disc


@router.post("/leads/{lead_id}/discovery", response_model=DiscoveryResponse, status_code=201)
async def create_discovery(lead_id: int, payload: DiscoveryCreate, db: AsyncSession = Depends(get_db)):
    # Verify lead exists
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    if not lead_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check if discovery already exists
    existing = await db.execute(select(Discovery).where(Discovery.lead_id == lead_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Discovery already exists for this lead")

    disc = Discovery(lead_id=lead_id, **payload.model_dump())
    db.add(disc)
    await db.flush()
    return disc


# ─── Proposals ───────────────────────────────────────────────────────────

@router.get("/leads/{lead_id}/proposals", response_model=List[ProposalResponse])
async def list_proposals(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Proposal).where(Proposal.lead_id == lead_id).order_by(Proposal.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/leads/{lead_id}/proposals", response_model=ProposalResponse, status_code=201)
async def create_proposal(lead_id: int, payload: ProposalCreate, db: AsyncSession = Depends(get_db)):
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    if not lead_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead not found")

    proposal = Proposal(lead_id=lead_id, **payload.model_dump())
    db.add(proposal)

    # Auto-update lead status
    lead = lead_result.scalar_one()
    lead.status = "proposal"

    await db.flush()
    return proposal


@router.post("/proposals/{proposal_id}/accept", response_model=ProposalResponse)
async def accept_proposal_endpoint(proposal_id: int, db: AsyncSession = Depends(get_db)):
    proposal = await accept_proposal(db, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    await event_bus.emit(Event(
        name="ProposalAccepted",
        payload={"proposal_id": proposal_id, "lead_id": proposal.lead_id},
        source_module="commercial_sales",
    ))
    return proposal


# ─── Contracts ───────────────────────────────────────────────────────────

@router.get("/contracts", response_model=List[ContractResponse])
async def list_contracts(
    contract_type: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Contract)
    if contract_type:
        stmt = stmt.where(Contract.contract_type == contract_type)
    if status:
        stmt = stmt.where(Contract.status == status)
    result = await db.execute(stmt.order_by(Contract.signed_at.desc()))
    return list(result.scalars().all())


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


# ─── SaaS Subscriptions ──────────────────────────────────────────────────

@router.post("/contracts/{contract_id}/subscription/activate", response_model=SubscriptionResponse)
async def activate_subscription_endpoint(
    contract_id: int,
    payload: SubscriptionActivate,
    db: AsyncSession = Depends(get_db),
):
    sub = await activate_subscription(db, contract_id, payload.tier, payload.seats)
    if not sub:
        raise HTTPException(
            status_code=400,
            detail="Could not activate. Contract must be of type 'subscription'.",
        )
    await event_bus.emit(Event(
        name="SubscriptionActivated",
        payload={"contract_id": contract_id, "tier": payload.tier, "seats": payload.seats},
        source_module="commercial_sales",
    ))
    return sub


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SaasSubscription).where(SaasSubscription.id == subscription_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.post("/subscriptions/{subscription_id}/churn", response_model=SubscriptionResponse)
async def churn_subscription_endpoint(
    subscription_id: int,
    payload: SubscriptionChurn,
    db: AsyncSession = Depends(get_db),
):
    sub = await churn_subscription(db, subscription_id, payload.reason)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await event_bus.emit(Event(
        name="SubscriptionChurned",
        payload={"subscription_id": subscription_id, "reason": payload.reason},
        source_module="commercial_sales",
    ))
    return sub


# ─── Onboarding ──────────────────────────────────────────────────────────

@router.post("/contracts/{contract_id}/onboarding", response_model=OnboardingResponse, status_code=201)
async def start_onboarding_endpoint(
    contract_id: int,
    payload: OnboardingStart,
    db: AsyncSession = Depends(get_db),
):
    onboarding = await start_onboarding(db, contract_id, payload.steps)
    if not onboarding:
        raise HTTPException(status_code=404, detail="Contract not found")
    return onboarding


@router.get("/onboarding/{onboarding_id}", response_model=OnboardingResponse)
async def get_onboarding(onboarding_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Onboarding).where(Onboarding.id == onboarding_id))
    onboarding = result.scalar_one_or_none()
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    return onboarding


@router.post("/onboarding/{onboarding_id}/step/{step_index}", response_model=OnboardingResponse)
async def complete_step(onboarding_id: int, step_index: int, db: AsyncSession = Depends(get_db)):
    onboarding = await complete_onboarding_step(db, onboarding_id, step_index)
    if not onboarding:
        raise HTTPException(status_code=400, detail="Invalid step index or onboarding not found")
    return onboarding


# ─── Account Plans ───────────────────────────────────────────────────────

@router.post("/contracts/{contract_id}/account-plans", response_model=AccountPlanResponse, status_code=201)
async def create_account_plan(contract_id: int, payload: AccountPlanCreate, db: AsyncSession = Depends(get_db)):
    contract_result = await db.execute(select(Contract).where(Contract.id == contract_id))
    if not contract_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Contract not found")
    plan = AccountPlan(contract_id=contract_id, **payload.model_dump())
    db.add(plan)
    await db.flush()
    return plan


@router.get("/contracts/{contract_id}/account-plans", response_model=List[AccountPlanResponse])
async def list_account_plans(contract_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AccountPlan).where(AccountPlan.contract_id == contract_id)
    )
    return list(result.scalars().all())


# ─── Retention Actions ───────────────────────────────────────────────────

@router.post(
    "/subscriptions/{subscription_id}/retention",
    response_model=RetentionActionResponse,
    status_code=201,
)
async def create_retention_action(
    subscription_id: int,
    payload: RetentionActionCreate,
    db: AsyncSession = Depends(get_db),
):
    sub_result = await db.execute(
        select(SaasSubscription).where(SaasSubscription.id == subscription_id)
    )
    if not sub_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Subscription not found")
    action = RetentionAction(subscription_id=subscription_id, **payload.model_dump())
    db.add(action)
    await db.flush()
    await event_bus.emit(Event(
        name="RetentionActionCreated",
        payload={"subscription_id": subscription_id, "action_type": payload.action_type},
        source_module="commercial_sales",
    ))
    return action


@router.get(
    "/subscriptions/{subscription_id}/retention",
    response_model=List[RetentionActionResponse],
)
async def list_retention_actions(subscription_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RetentionAction).where(RetentionAction.subscription_id == subscription_id)
    )
    return list(result.scalars().all())


# ─── ICP Matrix ──────────────────────────────────────────────────────────

@router.get("/icp-matrix", response_model=List[IcpMatrixResponse])
async def list_icp_matrix(
    industry: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(IcpMatrix)
    if industry:
        stmt = stmt.where(IcpMatrix.industry.ilike(f"%{industry}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/icp-matrix", response_model=IcpMatrixResponse, status_code=201)
async def create_icp_entry(payload: IcpMatrixCreate, db: AsyncSession = Depends(get_db)):
    entry = IcpMatrix(**payload.model_dump())
    db.add(entry)
    await db.flush()
    return entry
