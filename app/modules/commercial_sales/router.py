from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.core.pagination import PaginationParams, paginate
from app.modules.commercial_sales.domain.logic import (
    accept_proposal,
    activate_subscription,
    churn_subscription,
    complete_onboarding_step,
    qualify_lead,
    start_onboarding,
    terminate_service_contract,
    win_lead,
)
from app.modules.commercial_sales.domain.models import (
    AccountPlan,
    ChurnAnalysis,
    CompetitionMatrix,
    Contract,
    Discovery,
    IcpMatrix,
    Lead,
    MarketingPlan,
    Onboarding,
    ProjectHandoff,
    Proposal,
    Quote,
    RetentionAction,
    SaasSubscription,
    ServiceContractChurn,
)
from app.modules.commercial_sales.schemas.dto import (
    AccountPlanCreate,
    AccountPlanResponse,
    ChurnAnalysisCreate,
    ChurnAnalysisResponse,
    CompetitionMatrixCreate,
    CompetitionMatrixResponse,
    ContractCreate,
    ContractResponse,
    DiscoveryCreate,
    DiscoveryResponse,
    IcpMatrixCreate,
    IcpMatrixResponse,
    LeadCreate,
    LeadQualify,
    LeadResponse,
    LeadUpdate,
    MarketingPlanCreate,
    MarketingPlanResponse,
    OnboardingResponse,
    OnboardingStart,
    ProjectHandoffCreate,
    ProjectHandoffResponse,
    ProposalCreate,
    ProposalResponse,
    QuoteAccept,
    QuoteCreate,
    QuoteResponse,
    RetentionActionCreate,
    RetentionActionResponse,
    ServiceChurnAnalysisCreate,
    ServiceChurnAnalysisResponse,
    ServiceChurnTerminate,
    SubscriptionActivate,
    SubscriptionChurn,
    SubscriptionResponse,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# ─── Leads (CRM Pipeline) ────────────────────────────────────────────────

@router.get("/leads", response_model=List[LeadResponse])
async def list_leads(
    page: PaginationParams = Depends(),
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
    result = await db.execute(paginate(stmt.order_by(Lead.created_at.desc()), page))
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


@router.post("/leads/{lead_id}/qualify", response_model=LeadResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def qualify_lead_endpoint(lead_id: int, payload: LeadQualify, db: AsyncSession = Depends(get_db)):
    lead = await qualify_lead(db, lead_id, payload.icp_score)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/leads/{lead_id}/win", response_model=LeadResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
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
async def list_proposals(
    lead_id: int,
    page: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(paginate(
        select(Proposal).where(Proposal.lead_id == lead_id).order_by(Proposal.created_at.desc()),
        page,
    ))
    return list(result.scalars().all())


@router.post("/leads/{lead_id}/proposals", response_model=ProposalResponse, status_code=201)
async def create_proposal(lead_id: int, payload: ProposalCreate, db: AsyncSession = Depends(get_db)):
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    proposal = Proposal(lead_id=lead_id, **payload.model_dump())
    db.add(proposal)

    # Auto-update lead status
    lead.status = "proposal"

    await db.flush()
    return proposal


@router.post("/proposals/{proposal_id}/accept", response_model=ProposalResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
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
    page: PaginationParams = Depends(),
    contract_type: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Contract)
    if contract_type:
        stmt = stmt.where(Contract.contract_type == contract_type)
    if status:
        stmt = stmt.where(Contract.status == status)
    result = await db.execute(paginate(stmt.order_by(Contract.signed_at.desc()), page))
    return list(result.scalars().all())


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.post("/contracts", response_model=ContractResponse, status_code=201, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_contract(payload: ContractCreate, db: AsyncSession = Depends(get_db)):
    lead_result = await db.execute(select(Lead).where(Lead.id == payload.lead_id))
    if not lead_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead not found")

    contract = Contract(
        **payload.model_dump(),
        contract_number=f"CTR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        signed_at=datetime.now(timezone.utc),
    )
    db.add(contract)
    await db.flush()
    await event_bus.emit(Event(
        name="ContractCreated",
        payload={"contract_id": contract.id, "contract_type": payload.contract_type},
        source_module="commercial_sales",
    ))
    return contract


# ─── SaaS Subscriptions ──────────────────────────────────────────────────

@router.post("/contracts/{contract_id}/subscription/activate", response_model=SubscriptionResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
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


@router.post("/subscriptions/{subscription_id}/churn", response_model=SubscriptionResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
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

@router.post("/contracts/{contract_id}/onboarding", response_model=OnboardingResponse, status_code=201, dependencies=[Depends(RoleChecker("admin", "manager"))])
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


@router.post("/onboarding/{onboarding_id}/step/{step_index}", response_model=OnboardingResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def complete_step(onboarding_id: int, step_index: int, db: AsyncSession = Depends(get_db)):
    onboarding = await complete_onboarding_step(db, onboarding_id, step_index)
    if not onboarding:
        raise HTTPException(status_code=400, detail="Invalid step index or onboarding not found")
    return onboarding


# ─── Account Plans ───────────────────────────────────────────────────────

@router.post("/contracts/{contract_id}/account-plans", response_model=AccountPlanResponse, status_code=201, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_account_plan(contract_id: int, payload: AccountPlanCreate, db: AsyncSession = Depends(get_db)):
    contract_result = await db.execute(select(Contract).where(Contract.id == contract_id))
    if not contract_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Contract not found")
    plan = AccountPlan(contract_id=contract_id, **payload.model_dump())
    db.add(plan)
    await db.flush()
    return plan


@router.get("/contracts/{contract_id}/account-plans", response_model=List[AccountPlanResponse])
async def list_account_plans(
    contract_id: int,
    page: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(paginate(
        select(AccountPlan).where(AccountPlan.contract_id == contract_id).order_by(AccountPlan.id),
        page,
    ))
    return list(result.scalars().all())


# ─── Retention Actions ───────────────────────────────────────────────────

@router.post(
    "/subscriptions/{subscription_id}/retention",
    response_model=RetentionActionResponse,
    status_code=201,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
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
async def list_retention_actions(
    subscription_id: int,
    page: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(paginate(
        select(RetentionAction).where(RetentionAction.subscription_id == subscription_id).order_by(RetentionAction.id),
        page,
    ))
    return list(result.scalars().all())


# ─── ICP Matrix ──────────────────────────────────────────────────────────

@router.get("/icp-matrix", response_model=List[IcpMatrixResponse])
async def list_icp_matrix(
    page: PaginationParams = Depends(),
    industry: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(IcpMatrix)
    if industry:
        stmt = stmt.where(IcpMatrix.industry.ilike(f"%{industry}%"))
    result = await db.execute(paginate(stmt.order_by(IcpMatrix.id), page))
    return list(result.scalars().all())


@router.post("/icp-matrix", response_model=IcpMatrixResponse, status_code=201)
async def create_icp_entry(payload: IcpMatrixCreate, db: AsyncSession = Depends(get_db)):
    entry = IcpMatrix(**payload.model_dump())
    db.add(entry)
    await db.flush()
    return entry


# ─── Quotes (SOP-P3-004) ──────────────────────────────────────────────

@router.get("/leads/{lead_id}/quotes", response_model=List[QuoteResponse])
async def list_quotes(
    lead_id: int,
    page: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(paginate(
        select(Quote).where(Quote.lead_id == lead_id).order_by(Quote.created_at.desc()),
        page,
    ))
    return list(result.scalars().all())


@router.post("/leads/{lead_id}/quotes", response_model=QuoteResponse, status_code=201)
async def create_quote(lead_id: int, payload: QuoteCreate, db: AsyncSession = Depends(get_db)):
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    if not lead_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead not found")

    quote_number = f"QT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    quote = Quote(
        lead_id=lead_id,
        quote_number=quote_number,
        **payload.model_dump(),
    )

    # Auto-calculate tax and discount
    quote.tax_amount = quote.subtotal * quote.tax_rate / 100
    quote.discount_amount = quote.subtotal * quote.discount_percent / 100

    db.add(quote)
    await db.flush()
    return quote


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.post("/quotes/{quote_id}/send", response_model=QuoteResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def send_quote(quote_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft quotes can be sent")
    quote.status = "sent"
    quote.sent_at = datetime.now(timezone.utc)
    await db.flush()
    return quote


@router.post("/quotes/{quote_id}/accept", response_model=QuoteResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def accept_quote_endpoint(quote_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.status != "sent":
        raise HTTPException(status_code=400, detail="Only sent quotes can be accepted")
    quote.status = "accepted"
    quote.accepted_at = datetime.now(timezone.utc)
    await db.flush()
    await event_bus.emit(Event(
        name="QuoteAccepted",
        payload={"quote_id": quote_id, "lead_id": quote.lead_id},
        source_module="commercial_sales",
    ))
    return quote


# ─── Project Handoffs (SOP-P3-006) ─────────────────────────────────────

@router.post("/contracts/{contract_id}/handoffs", response_model=ProjectHandoffResponse, status_code=201, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_handoff(
    contract_id: int,
    payload: ProjectHandoffCreate,
    db: AsyncSession = Depends(get_db),
):
    contract_result = await db.execute(select(Contract).where(Contract.id == contract_id))
    if not contract_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Contract not found")

    handoff = ProjectHandoff(contract_id=contract_id, **payload.model_dump())
    db.add(handoff)
    await db.flush()
    return handoff


@router.get("/contracts/{contract_id}/handoffs", response_model=List[ProjectHandoffResponse])
async def list_handoffs(
    contract_id: int,
    page: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(paginate(
        select(ProjectHandoff).where(ProjectHandoff.contract_id == contract_id).order_by(ProjectHandoff.id),
        page,
    ))
    return list(result.scalars().all())


@router.get("/handoffs/{handoff_id}", response_model=ProjectHandoffResponse)
async def get_handoff(handoff_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProjectHandoff).where(ProjectHandoff.id == handoff_id))
    handoff = result.scalar_one_or_none()
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return handoff


@router.post("/handoffs/{handoff_id}/complete", response_model=ProjectHandoffResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def complete_handoff(
    handoff_id: int,
    signed_by_sales: str = Query(...),
    signed_by_pm: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProjectHandoff).where(ProjectHandoff.id == handoff_id))
    handoff = result.scalar_one_or_none()
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")
    if handoff.status != "in_progress":
        raise HTTPException(status_code=400, detail="Handoff must be in_progress to complete")

    handoff.status = "completed"
    handoff.signed_by_sales = signed_by_sales
    handoff.signed_by_pm = signed_by_pm
    handoff.signed_at = datetime.now(timezone.utc)
    await db.flush()
    return handoff


# ─── Churn Analysis (SOP-P3-009) ───────────────────────────────────────

@router.post("/subscriptions/{subscription_id}/churn-analysis", response_model=ChurnAnalysisResponse, status_code=201, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_churn_analysis(
    subscription_id: int,
    payload: ChurnAnalysisCreate,
    db: AsyncSession = Depends(get_db),
):
    sub_result = await db.execute(
        select(SaasSubscription).where(SaasSubscription.id == subscription_id)
    )
    if not sub_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Subscription not found")

    analysis = ChurnAnalysis(subscription_id=subscription_id, **payload.model_dump())
    db.add(analysis)
    await db.flush()
    return analysis


@router.get("/subscriptions/{subscription_id}/churn-analysis", response_model=List[ChurnAnalysisResponse])
async def list_churn_analyses(
    subscription_id: int,
    page: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(paginate(
        select(ChurnAnalysis).where(ChurnAnalysis.subscription_id == subscription_id).order_by(ChurnAnalysis.analysis_date.desc()),
        page,
    ))
    return list(result.scalars().all())


@router.get("/churn-analysis/{analysis_id}", response_model=ChurnAnalysisResponse)
async def get_churn_analysis(analysis_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChurnAnalysis).where(ChurnAnalysis.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Churn analysis not found")
    return analysis


# ─── Service Contract Churn (SERVICIOS) ──────────────────────────────────

@router.post("/contracts/{contract_id}/terminate", response_model=ContractResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def terminate_contract_endpoint(
    contract_id: int,
    payload: ServiceChurnTerminate,
    db: AsyncSession = Depends(get_db),
):
    contract = await terminate_service_contract(db, contract_id, payload.reason)
    if not contract:
        raise HTTPException(
            status_code=400,
            detail="Could not terminate. Contract must be of type 'sow'.",
        )
    await event_bus.emit(Event(
        name="ServiceContractTerminated",
        payload={"contract_id": contract_id, "reason": payload.reason},
        source_module="commercial_sales",
    ))
    return contract


@router.post("/contracts/{contract_id}/service-churn", response_model=ServiceChurnAnalysisResponse, status_code=201, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_service_churn_analysis(
    contract_id: int,
    payload: ServiceChurnAnalysisCreate,
    db: AsyncSession = Depends(get_db),
):
    contract_result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    if not contract_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Contract not found")

    analysis = ServiceContractChurn(contract_id=contract_id, **payload.model_dump())
    db.add(analysis)
    await db.flush()
    return analysis


@router.get("/contracts/{contract_id}/service-churn", response_model=List[ServiceChurnAnalysisResponse])
async def list_service_churn_analyses(
    contract_id: int,
    page: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(paginate(
        select(ServiceContractChurn).where(ServiceContractChurn.contract_id == contract_id).order_by(ServiceContractChurn.analysis_date.desc()),
        page,
    ))
    return list(result.scalars().all())


@router.get("/service-churn/{analysis_id}", response_model=ServiceChurnAnalysisResponse)
async def get_service_churn_analysis(analysis_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceContractChurn).where(ServiceContractChurn.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Service churn analysis not found")
    return analysis


# ─── Marketing Plans (PLN-P3-001) ──────────────────────────────────────

@router.get("/marketing-plans", response_model=List[MarketingPlanResponse])
async def list_marketing_plans(
    page: PaginationParams = Depends(),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MarketingPlan)
    if status:
        stmt = stmt.where(MarketingPlan.status == status)
    result = await db.execute(paginate(stmt.order_by(MarketingPlan.created_at.desc()), page))
    return list(result.scalars().all())


@router.post("/marketing-plans", response_model=MarketingPlanResponse, status_code=201)
async def create_marketing_plan(payload: MarketingPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = MarketingPlan(**payload.model_dump())
    db.add(plan)
    await db.flush()
    return plan


@router.get("/marketing-plans/{plan_id}", response_model=MarketingPlanResponse)
async def get_marketing_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MarketingPlan).where(MarketingPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Marketing plan not found")
    return plan


@router.patch("/marketing-plans/{plan_id}", response_model=MarketingPlanResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_marketing_plan(
    plan_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MarketingPlan).where(MarketingPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Marketing plan not found")
    for field, value in payload.items():
        if hasattr(plan, field):
            setattr(plan, field, value)
    await db.flush()
    return plan


# ─── Competition Matrix (MAT-P3-002) ───────────────────────────────────

@router.get("/competition-matrix", response_model=List[CompetitionMatrixResponse])
async def list_competition_matrix(
    page: PaginationParams = Depends(),
    product_category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CompetitionMatrix)
    if product_category:
        stmt = stmt.where(CompetitionMatrix.product_category.ilike(f"%{product_category}%"))
    result = await db.execute(paginate(stmt.order_by(CompetitionMatrix.id), page))
    return list(result.scalars().all())


@router.post("/competition-matrix", response_model=CompetitionMatrixResponse, status_code=201)
async def create_competition_entry(payload: CompetitionMatrixCreate, db: AsyncSession = Depends(get_db)):
    entry = CompetitionMatrix(**payload.model_dump())
    db.add(entry)
    await db.flush()
    return entry


@router.get("/competition-matrix/{entry_id}", response_model=CompetitionMatrixResponse)
async def get_competition_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompetitionMatrix).where(CompetitionMatrix.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Competition entry not found")
    return entry


@router.patch("/competition-matrix/{entry_id}", response_model=CompetitionMatrixResponse)
async def update_competition_entry(
    entry_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CompetitionMatrix).where(CompetitionMatrix.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Competition entry not found")
    for field, value in payload.items():
        if hasattr(entry, field):
            setattr(entry, field, value)
    await db.flush()
    return entry
