"""Web routes for Commercial Sales — Leads, Discovery, Proposals, Contracts, Subscriptions, Onboarding, Account Plans, Retention, ICP."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
from app.web.deps import get_current_user_from_session
from app.web.utils import render

router = APIRouter(prefix="/commercial", tags=["Web — Commercial Sales"])

_PER_PAGE = 20


# ─── Helpers ──────────────────────────────────────────────────────────────


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


# ─── Root ─────────────────────────────────────────────────────────────────


@router.get("")
async def commercial_root():
    """Sidebar links to /commercial — redirect to leads list."""
    return _redirect("/commercial/leads")


# ─── Leads ────────────────────────────────────────────────────────────────


@router.get("/leads")
async def list_leads(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    product_line: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Lead)
    count_stmt = select(func.count()).select_from(Lead.__table__)

    if search:
        stmt = stmt.where(
            or_(
                Lead.company.ilike(f"%{search}%"),
                Lead.contact_name.ilike(f"%{search}%"),
                Lead.contact_email.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                Lead.company.ilike(f"%{search}%"),
                Lead.contact_name.ilike(f"%{search}%"),
                Lead.contact_email.ilike(f"%{search}%"),
            )
        )
    if status:
        stmt = stmt.where(Lead.status == status)
        count_stmt = count_stmt.where(Lead.status == status)
    if product_line:
        stmt = stmt.where(Lead.product_line == product_line)
        count_stmt = count_stmt.where(Lead.product_line == product_line)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(Lead.created_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/commercial/leads.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "status": status,
        "product_line": product_line,
        "page_title": "Leads",
    })


@router.get("/leads/table")
async def leads_table(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    product_line: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Lead)
    count_stmt = select(func.count()).select_from(Lead.__table__)

    if search:
        stmt = stmt.where(
            or_(
                Lead.company.ilike(f"%{search}%"),
                Lead.contact_name.ilike(f"%{search}%"),
                Lead.contact_email.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                Lead.company.ilike(f"%{search}%"),
                Lead.contact_name.ilike(f"%{search}%"),
                Lead.contact_email.ilike(f"%{search}%"),
            )
        )
    if status:
        stmt = stmt.where(Lead.status == status)
        count_stmt = count_stmt.where(Lead.status == status)
    if product_line:
        stmt = stmt.where(Lead.product_line == product_line)
        count_stmt = count_stmt.where(Lead.product_line == product_line)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(Lead.created_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/commercial/_leads_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "status": status,
        "product_line": product_line,
    })


@router.get("/leads/create")
async def create_lead_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/commercial/lead_create.html", {
        "page_title": "Create Lead",
    })


@router.get("/leads/{lead_id}")
async def detail_lead(
    request: Request,
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/commercial/leads")
    return render(request, "pages/commercial/lead_detail.html", {
        "item": item,
        "page_title": f"Lead — {item.company}",
    })


@router.post("/leads")
async def create_lead(
    request: Request,
    company: str = Form(...),
    contact_name: str = Form(...),
    contact_email: str = Form(...),
    contact_phone: str = Form(""),
    source: str = Form(...),
    product_line: str = Form(...),
    estimated_value: Optional[float] = Form(None),
    assigned_to: str = Form(""),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = Lead(
        company=company,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone or None,
        source=source,
        product_line=product_line,
        estimated_value=Decimal(str(estimated_value)) if estimated_value else None,
        assigned_to=assigned_to or None,
        notes=notes or None,
        status="new",
    )
    db.add(item)
    await db.commit()
    return _redirect("/commercial/leads")


@router.post("/leads/{lead_id}/qualify")
async def qualify_lead(
    request: Request,
    lead_id: int,
    icp_match_score: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "qualified"
        if icp_match_score is not None:
            item.icp_match_score = icp_match_score
        await db.commit()
    return _redirect(f"/commercial/leads/{lead_id}")


@router.post("/leads/{lead_id}/win")
async def win_lead(
    request: Request,
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "won"
        await db.commit()
    return _redirect(f"/commercial/leads/{lead_id}")


# ─── Discovery ────────────────────────────────────────────────────────────


@router.get("/leads/{lead_id}/discovery")
async def detail_discovery(
    request: Request,
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        return _redirect("/commercial/leads")

    disc_result = await db.execute(select(Discovery).where(Discovery.lead_id == lead_id))
    discovery = disc_result.scalar_one_or_none()

    return render(request, "pages/commercial/discovery_detail.html", {
        "item": discovery,
        "lead": lead,
        "page_title": f"Discovery — {lead.company}",
    })


@router.get("/leads/{lead_id}/discovery/create")
async def create_discovery_form(
    request: Request,
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        return _redirect("/commercial/leads")
    return render(request, "pages/commercial/discovery_create.html", {
        "lead": lead,
        "page_title": f"Discovery — {lead.company}",
    })


@router.post("/leads/{lead_id}/discovery")
async def create_discovery(
    request: Request,
    lead_id: int,
    needs: str = Form(...),
    budget_range: str = Form(""),
    timeline: str = Form(""),
    decision_criteria: str = Form(""),
    pain_points: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = Discovery(
        lead_id=lead_id,
        needs=needs,
        budget_range=budget_range or None,
        timeline=timeline or None,
        decision_criteria=decision_criteria or None,
        pain_points=pain_points or None,
        recorded_by=user.username,
    )
    db.add(item)
    # Update lead status to qualifying
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if lead and lead.status.value == "new":
        lead.status = "qualifying"
    await db.commit()
    return _redirect(f"/commercial/leads/{lead_id}/discovery")


# ─── Proposals ────────────────────────────────────────────────────────────


@router.get("/leads/{lead_id}/proposals")
async def list_proposals(
    request: Request,
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        return _redirect("/commercial/leads")

    stmt = select(Proposal).where(Proposal.lead_id == lead_id).order_by(Proposal.created_at.desc())
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/commercial/proposals.html", {
        "items": items,
        "lead": lead,
        "page_title": f"Proposals — {lead.company}",
    })


@router.get("/leads/{lead_id}/proposals/create")
async def create_proposal_form(
    request: Request,
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        return _redirect("/commercial/leads")
    return render(request, "pages/commercial/proposal_create.html", {
        "lead": lead,
        "page_title": f"New Proposal — {lead.company}",
    })


@router.get("/proposals/{proposal_id}")
async def detail_proposal(
    request: Request,
    proposal_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/commercial/leads")
    return render(request, "pages/commercial/proposal_detail.html", {
        "item": item,
        "page_title": f"Proposal v{item.version}",
    })


@router.post("/leads/{lead_id}/proposals")
async def create_proposal(
    request: Request,
    lead_id: int,
    version: str = Form("1.0"),
    total_amount: float = Form(...),
    valid_until: Optional[date] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = Proposal(
        lead_id=lead_id,
        version=version,
        total_amount=Decimal(str(total_amount)),
        valid_until=valid_until,
        created_by=user.username,
        status="draft",
    )
    db.add(item)
    # Update lead status
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if lead and lead.status.value in ("new", "qualifying", "qualified"):
        lead.status = "proposal"
    await db.commit()
    return _redirect(f"/commercial/leads/{lead_id}/proposals")


@router.post("/proposals/{proposal_id}/accept")
async def accept_proposal(
    request: Request,
    proposal_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "accepted"
        item.accepted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/commercial/proposals/{proposal_id}")


# ─── Contracts ────────────────────────────────────────────────────────────


@router.get("/contracts")
async def list_contracts(
    request: Request,
    page: int = 1,
    search: str = "",
    contract_type: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Contract)
    count_stmt = select(func.count()).select_from(Contract.__table__)

    if search:
        stmt = stmt.where(
            or_(
                Contract.contract_number.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                Contract.contract_number.ilike(f"%{search}%"),
            )
        )
    if contract_type:
        stmt = stmt.where(Contract.contract_type == contract_type)
        count_stmt = count_stmt.where(Contract.contract_type == contract_type)
    if status:
        stmt = stmt.where(Contract.status == status)
        count_stmt = count_stmt.where(Contract.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(Contract.signed_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/commercial/contracts.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "contract_type": contract_type,
        "status": status,
        "page_title": "Contracts",
    })


@router.get("/contracts/table")
async def contracts_table(
    request: Request,
    page: int = 1,
    search: str = "",
    contract_type: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Contract)
    count_stmt = select(func.count()).select_from(Contract.__table__)

    if search:
        stmt = stmt.where(
            or_(
                Contract.contract_number.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                Contract.contract_number.ilike(f"%{search}%"),
            )
        )
    if contract_type:
        stmt = stmt.where(Contract.contract_type == contract_type)
        count_stmt = count_stmt.where(Contract.contract_type == contract_type)
    if status:
        stmt = stmt.where(Contract.status == status)
        count_stmt = count_stmt.where(Contract.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(Contract.signed_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/commercial/_contracts_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "contract_type": contract_type,
        "status": status,
    })


@router.get("/contracts/{contract_id}")
async def detail_contract(
    request: Request,
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/commercial/contracts")
    return render(request, "pages/commercial/contract_detail.html", {
        "item": item,
        "page_title": f"Contract {item.contract_number}",
    })


# ─── SaaS Subscriptions ──────────────────────────────────────────────────


@router.get("/contracts/{contract_id}/subscription")
async def detail_subscription(
    request: Request,
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    contract_result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = contract_result.scalar_one_or_none()
    if not contract:
        return _redirect("/commercial/contracts")

    sub_result = await db.execute(select(SaasSubscription).where(SaasSubscription.contract_id == contract_id))
    subscription = sub_result.scalar_one_or_none()

    return render(request, "pages/commercial/subscription_detail.html", {
        "item": subscription,
        "contract": contract,
        "page_title": f"Subscription — {contract.contract_number}",
    })


@router.post("/subscriptions/{subscription_id}/activate")
async def activate_subscription(
    request: Request,
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(SaasSubscription).where(SaasSubscription.id == subscription_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "active"
        item.activated_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/commercial/subscriptions/{subscription_id}")


@router.post("/subscriptions/{subscription_id}/churn")
async def churn_subscription(
    request: Request,
    subscription_id: int,
    churn_reason: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(SaasSubscription).where(SaasSubscription.id == subscription_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "churned"
        item.churned_at = datetime.now(timezone.utc)
        item.churn_reason = churn_reason or None
        await db.commit()
    return _redirect(f"/commercial/subscriptions/{subscription_id}")


# ─── Onboarding ───────────────────────────────────────────────────────────


@router.get("/contracts/{contract_id}/onboarding")
async def detail_onboarding(
    request: Request,
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    contract_result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = contract_result.scalar_one_or_none()
    if not contract:
        return _redirect("/commercial/contracts")

    ob_result = await db.execute(select(Onboarding).where(Onboarding.contract_id == contract_id))
    onboarding = ob_result.scalar_one_or_none()

    return render(request, "pages/commercial/onboarding_detail.html", {
        "item": onboarding,
        "contract": contract,
        "page_title": f"Onboarding — {contract.contract_number}",
    })


@router.post("/contracts/{contract_id}/onboarding/start")
async def start_onboarding(
    request: Request,
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    # Check if onboarding already exists
    existing = await db.execute(select(Onboarding).where(Onboarding.contract_id == contract_id))
    if existing.scalar_one_or_none():
        return _redirect(f"/commercial/contracts/{contract_id}/onboarding")

    item = Onboarding(
        contract_id=contract_id,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
        steps=[],
    )
    db.add(item)
    await db.commit()
    return _redirect(f"/commercial/contracts/{contract_id}/onboarding")


@router.post("/onboarding/{onboarding_id}/step")
async def complete_onboarding_step(
    request: Request,
    onboarding_id: int,
    step_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(Onboarding).where(Onboarding.id == onboarding_id))
    item = result.scalar_one_or_none()
    if item:
        steps = item.steps or []
        steps.append({
            "step": step_name,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "assigned_to": user.username,
        })
        item.steps = steps
        await db.commit()
    return _redirect(f"/commercial/onboarding/{onboarding_id}")


# ─── Account Plans ────────────────────────────────────────────────────────


@router.get("/contracts/{contract_id}/account-plans")
async def list_account_plans(
    request: Request,
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    contract_result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = contract_result.scalar_one_or_none()
    if not contract:
        return _redirect("/commercial/contracts")

    stmt = select(AccountPlan).where(AccountPlan.contract_id == contract_id).order_by(AccountPlan.created_at.desc())
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/commercial/account_plans.html", {
        "items": items,
        "contract": contract,
        "page_title": f"Account Plans — {contract.contract_number}",
    })


@router.get("/contracts/{contract_id}/account-plans/create")
async def create_account_plan_form(
    request: Request,
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    contract_result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = contract_result.scalar_one_or_none()
    if not contract:
        return _redirect("/commercial/contracts")
    return render(request, "pages/commercial/account_plan_create.html", {
        "contract": contract,
        "page_title": f"New Account Plan — {contract.contract_number}",
    })


@router.get("/account-plans/{plan_id}")
async def detail_account_plan(
    request: Request,
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(AccountPlan).where(AccountPlan.id == plan_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/commercial/contracts")
    return render(request, "pages/commercial/account_plan_detail.html", {
        "item": item,
        "page_title": f"Account Plan #{item.id}",
    })


@router.post("/contracts/{contract_id}/account-plans")
async def create_account_plan(
    request: Request,
    contract_id: int,
    goals: str = Form(...),
    review_date: Optional[date] = Form(None),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = AccountPlan(
        contract_id=contract_id,
        goals=goals,
        review_date=review_date,
        notes=notes or None,
    )
    db.add(item)
    await db.commit()
    return _redirect(f"/commercial/contracts/{contract_id}/account-plans")


# ─── Retention Actions ───────────────────────────────────────────────────


@router.get("/subscriptions/{subscription_id}/retention")
async def list_retention_actions(
    request: Request,
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    sub_result = await db.execute(select(SaasSubscription).where(SaasSubscription.id == subscription_id))
    subscription = sub_result.scalar_one_or_none()
    if not subscription:
        return _redirect("/commercial/contracts")

    stmt = select(RetentionAction).where(
        RetentionAction.subscription_id == subscription_id
    ).order_by(RetentionAction.created_at.desc())
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/commercial/retention_actions.html", {
        "items": items,
        "subscription": subscription,
        "page_title": f"Retention Actions — Subscription #{subscription_id}",
    })


@router.get("/subscriptions/{subscription_id}/retention/create")
async def create_retention_action_form(
    request: Request,
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    sub_result = await db.execute(select(SaasSubscription).where(SaasSubscription.id == subscription_id))
    subscription = sub_result.scalar_one_or_none()
    if not subscription:
        return _redirect("/commercial/contracts")
    return render(request, "pages/commercial/retention_action_create.html", {
        "subscription": subscription,
        "page_title": f"New Retention Action — Subscription #{subscription_id}",
    })


@router.get("/retention/{action_id}")
async def detail_retention_action(
    request: Request,
    action_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(RetentionAction).where(RetentionAction.id == action_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/commercial/contracts")
    return render(request, "pages/commercial/retention_action_detail.html", {
        "item": item,
        "page_title": f"Retention Action — {item.action_type}",
    })


@router.post("/subscriptions/{subscription_id}/retention")
async def create_retention_action(
    request: Request,
    subscription_id: int,
    action_type: str = Form(...),
    description: str = Form(...),
    assigned_to: str = Form(...),
    deadline: Optional[date] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = RetentionAction(
        subscription_id=subscription_id,
        action_type=action_type,
        description=description,
        assigned_to=assigned_to,
        deadline=deadline,
        status="planned",
    )
    db.add(item)
    await db.commit()
    return _redirect(f"/commercial/subscriptions/{subscription_id}/retention")


# ─── ICP Matrix ───────────────────────────────────────────────────────────


@router.get("/icp")
async def list_icp(
    request: Request,
    page: int = 1,
    search: str = "",
    industry: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(IcpMatrix)
    count_stmt = select(func.count()).select_from(IcpMatrix.__table__)

    if search:
        stmt = stmt.where(
            or_(
                IcpMatrix.industry.ilike(f"%{search}%"),
                IcpMatrix.role.ilike(f"%{search}%"),
                IcpMatrix.company_size.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                IcpMatrix.industry.ilike(f"%{search}%"),
                IcpMatrix.role.ilike(f"%{search}%"),
                IcpMatrix.company_size.ilike(f"%{search}%"),
            )
        )
    if industry:
        stmt = stmt.where(IcpMatrix.industry == industry)
        count_stmt = count_stmt.where(IcpMatrix.industry == industry)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(IcpMatrix.industry).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/commercial/icp.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "industry": industry,
        "page_title": "ICP Matrix",
    })


@router.get("/icp/table")
async def icp_table(
    request: Request,
    page: int = 1,
    search: str = "",
    industry: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(IcpMatrix)
    count_stmt = select(func.count()).select_from(IcpMatrix.__table__)

    if search:
        stmt = stmt.where(
            or_(
                IcpMatrix.industry.ilike(f"%{search}%"),
                IcpMatrix.role.ilike(f"%{search}%"),
                IcpMatrix.company_size.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                IcpMatrix.industry.ilike(f"%{search}%"),
                IcpMatrix.role.ilike(f"%{search}%"),
                IcpMatrix.company_size.ilike(f"%{search}%"),
            )
        )
    if industry:
        stmt = stmt.where(IcpMatrix.industry == industry)
        count_stmt = count_stmt.where(IcpMatrix.industry == industry)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(IcpMatrix.industry).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/commercial/_icp_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "industry": industry,
    })


@router.get("/icp/create")
async def create_icp_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/commercial/icp_create.html", {
        "page_title": "Create ICP Profile",
    })


@router.get("/icp/{matrix_id}")
async def detail_icp(
    request: Request,
    matrix_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(IcpMatrix).where(IcpMatrix.id == matrix_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/commercial/icp")
    return render(request, "pages/commercial/icp_detail.html", {
        "item": item,
        "page_title": f"ICP — {item.industry}",
    })


@router.post("/icp")
async def create_icp(
    request: Request,
    industry: str = Form(...),
    company_size: str = Form(...),
    role: str = Form(...),
    pain_points: str = Form(...),
    fit_score: int = Form(50),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = IcpMatrix(
        industry=industry,
        company_size=company_size,
        role=role,
        pain_points=pain_points,
        fit_score=fit_score,
        is_active=True,
    )
    db.add(item)
    await db.commit()
    return _redirect("/commercial/icp")
