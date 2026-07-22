"""Web routes for Strategic Planning — Policies, Objectives, Marketing, Reviews, Scope."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.strategic_planning.domain.models import (
    ManagementReviewReport,
    MarketingPlan,
    QualityObjective,
    QualityPolicy,
    QmsScope,
    StrategyReview,
)
from app.web.deps import get_current_user_from_session
from app.web.utils import render

router = APIRouter(prefix="/strategic", tags=["Web — Strategic Planning"])

_PER_PAGE = 20


# ─── Helpers ──────────────────────────────────────────────────────────────


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


# ─── Quality Policies ────────────────────────────────────────────────────


@router.get("")
async def strategic_root():
    """Sidebar links to /strategic — redirect to policies list."""
    return _redirect("/strategic/policies")


@router.get("/policies")
async def list_policies(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(QualityPolicy)
    count_stmt = select(func.count()).select_from(QualityPolicy.__table__)

    if search:
        stmt = stmt.where(
            or_(
                QualityPolicy.code.ilike(f"%{search}%"),
                QualityPolicy.title.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                QualityPolicy.code.ilike(f"%{search}%"),
                QualityPolicy.title.ilike(f"%{search}%"),
            )
        )
    if status:
        stmt = stmt.where(QualityPolicy.status == status)
        count_stmt = count_stmt.where(QualityPolicy.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(QualityPolicy.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/strategic/policies.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "status": status,
        "page_title": "Quality Policies",
    })


@router.get("/policies/table")
async def policies_table(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(QualityPolicy)
    count_stmt = select(func.count()).select_from(QualityPolicy.__table__)

    if search:
        stmt = stmt.where(
            or_(
                QualityPolicy.code.ilike(f"%{search}%"),
                QualityPolicy.title.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                QualityPolicy.code.ilike(f"%{search}%"),
                QualityPolicy.title.ilike(f"%{search}%"),
            )
        )
    if status:
        stmt = stmt.where(QualityPolicy.status == status)
        count_stmt = count_stmt.where(QualityPolicy.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(QualityPolicy.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/strategic/_policies_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "status": status,
    })


@router.get("/policies/create")
async def create_policy_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/strategic/policy_create.html", {
        "page_title": "Create Quality Policy",
    })


@router.get("/policies/{policy_id}")
async def detail_policy(
    request: Request,
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QualityPolicy).where(QualityPolicy.id == policy_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/strategic/policies")
    return render(request, "pages/strategic/policy_detail.html", {
        "item": item,
        "page_title": f"Policy {item.code}",
    })


@router.post("/policies")
async def create_policy(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    content: str = Form(""),
    version: str = Form("1.0"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = QualityPolicy(
        code=code,
        title=title,
        content=content,
        version=version,
        status="draft",
    )
    db.add(item)
    await db.commit()
    return _redirect("/strategic/policies")


@router.post("/policies/{policy_id}/approve")
async def approve_policy(
    request: Request,
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QualityPolicy).where(QualityPolicy.id == policy_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "approved"
        item.approved_by = user.username
        item.approved_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/strategic/policies/{policy_id}")


@router.post("/policies/{policy_id}/review")
async def review_policy(
    request: Request,
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QualityPolicy).where(QualityPolicy.id == policy_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "reviewed"
        await db.commit()
    return _redirect(f"/strategic/policies/{policy_id}")


@router.post("/policies/{policy_id}/obsolete")
async def obsolete_policy(
    request: Request,
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QualityPolicy).where(QualityPolicy.id == policy_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "obsolete"
        await db.commit()
    return _redirect(f"/strategic/policies/{policy_id}")


# ─── Quality Objectives ─────────────────────────────────────────────────


@router.get("/objectives")
async def list_objectives(
    request: Request,
    page: int = 1,
    search: str = "",
    year: Optional[int] = None,
    process_code: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(QualityObjective)
    count_stmt = select(func.count()).select_from(QualityObjective.__table__)

    if search:
        stmt = stmt.where(
            or_(
                QualityObjective.code.ilike(f"%{search}%"),
                QualityObjective.objective.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                QualityObjective.code.ilike(f"%{search}%"),
                QualityObjective.objective.ilike(f"%{search}%"),
            )
        )
    if year:
        stmt = stmt.where(QualityObjective.year == year)
        count_stmt = count_stmt.where(QualityObjective.year == year)
    if process_code:
        stmt = stmt.where(QualityObjective.process_code == process_code)
        count_stmt = count_stmt.where(QualityObjective.process_code == process_code)
    if status:
        stmt = stmt.where(QualityObjective.status == status)
        count_stmt = count_stmt.where(QualityObjective.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(QualityObjective.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/strategic/objectives.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "year": year,
        "process_code": process_code,
        "status": status,
        "page_title": "Quality Objectives",
    })


@router.get("/objectives/table")
async def objectives_table(
    request: Request,
    page: int = 1,
    search: str = "",
    year: Optional[int] = None,
    process_code: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(QualityObjective)
    count_stmt = select(func.count()).select_from(QualityObjective.__table__)

    if search:
        stmt = stmt.where(
            or_(
                QualityObjective.code.ilike(f"%{search}%"),
                QualityObjective.objective.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                QualityObjective.code.ilike(f"%{search}%"),
                QualityObjective.objective.ilike(f"%{search}%"),
            )
        )
    if year:
        stmt = stmt.where(QualityObjective.year == year)
        count_stmt = count_stmt.where(QualityObjective.year == year)
    if process_code:
        stmt = stmt.where(QualityObjective.process_code == process_code)
        count_stmt = count_stmt.where(QualityObjective.process_code == process_code)
    if status:
        stmt = stmt.where(QualityObjective.status == status)
        count_stmt = count_stmt.where(QualityObjective.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(QualityObjective.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/strategic/_objectives_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "year": year,
        "process_code": process_code,
        "status": status,
    })


@router.get("/objectives/create")
async def create_objective_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/strategic/objective_create.html", {
        "page_title": "Create Quality Objective",
    })


@router.get("/objectives/{objective_id}")
async def detail_objective(
    request: Request,
    objective_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QualityObjective).where(QualityObjective.id == objective_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/strategic/objectives")

    # Calculate progress percentage for the template
    progress = 0
    if item.target_value and item.target_value > 0 and item.actual_value is not None:
        progress = min(100, round((item.actual_value / item.target_value) * 100))

    return render(request, "pages/strategic/objective_detail.html", {
        "item": item,
        "progress": progress,
        "page_title": f"Objective {item.code}",
    })


@router.post("/objectives")
async def create_objective(
    request: Request,
    code: str = Form(...),
    objective: str = Form(...),
    process_code: str = Form(...),
    target_value: float = Form(...),
    metric_unit: str = Form(...),
    year: int = Form(...),
    responsible: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = QualityObjective(
        code=code,
        objective=objective,
        process_code=process_code,
        target_value=target_value,
        metric_unit=metric_unit,
        year=year,
        responsible=responsible,
        status="on_track",
    )
    db.add(item)
    await db.commit()
    return _redirect("/strategic/objectives")


@router.post("/objectives/{objective_id}/progress")
async def update_objective_progress(
    request: Request,
    objective_id: int,
    actual_value: float = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QualityObjective).where(QualityObjective.id == objective_id))
    item = result.scalar_one_or_none()
    if item:
        item.actual_value = actual_value
        # Auto-calculate status from progress
        if item.target_value and item.target_value > 0:
            pct = (actual_value / item.target_value) * 100
            if pct >= 100:
                item.status = "achieved"
            elif pct >= 80:
                item.status = "on_track"
            elif pct >= 50:
                item.status = "at_risk"
            else:
                item.status = "behind"
        await db.commit()
    return _redirect(f"/strategic/objectives/{objective_id}")


# ─── Marketing Plans ────────────────────────────────────────────────────


@router.get("/marketing")
async def list_marketing(
    request: Request,
    page: int = 1,
    search: str = "",
    year: Optional[int] = None,
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(MarketingPlan)
    count_stmt = select(func.count()).select_from(MarketingPlan.__table__)

    if search:
        stmt = stmt.where(
            or_(
                MarketingPlan.code.ilike(f"%{search}%"),
                MarketingPlan.title.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                MarketingPlan.code.ilike(f"%{search}%"),
                MarketingPlan.title.ilike(f"%{search}%"),
            )
        )
    if year:
        stmt = stmt.where(MarketingPlan.year == year)
        count_stmt = count_stmt.where(MarketingPlan.year == year)
    if status:
        stmt = stmt.where(MarketingPlan.status == status)
        count_stmt = count_stmt.where(MarketingPlan.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(MarketingPlan.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/strategic/marketing.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "year": year,
        "status": status,
        "page_title": "Marketing Plans",
    })


@router.get("/marketing/table")
async def marketing_table(
    request: Request,
    page: int = 1,
    search: str = "",
    year: Optional[int] = None,
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(MarketingPlan)
    count_stmt = select(func.count()).select_from(MarketingPlan.__table__)

    if search:
        stmt = stmt.where(
            or_(
                MarketingPlan.code.ilike(f"%{search}%"),
                MarketingPlan.title.ilike(f"%{search}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                MarketingPlan.code.ilike(f"%{search}%"),
                MarketingPlan.title.ilike(f"%{search}%"),
            )
        )
    if year:
        stmt = stmt.where(MarketingPlan.year == year)
        count_stmt = count_stmt.where(MarketingPlan.year == year)
    if status:
        stmt = stmt.where(MarketingPlan.status == status)
        count_stmt = count_stmt.where(MarketingPlan.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(MarketingPlan.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/strategic/_marketing_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "year": year,
        "status": status,
    })


@router.get("/marketing/create")
async def create_marketing_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/strategic/marketing_create.html", {
        "page_title": "Create Marketing Plan",
    })


@router.get("/marketing/{plan_id}")
async def detail_marketing(
    request: Request,
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(MarketingPlan).where(MarketingPlan.id == plan_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/strategic/marketing")
    return render(request, "pages/strategic/marketing_detail.html", {
        "item": item,
        "page_title": f"Marketing Plan {item.code}",
    })


@router.post("/marketing")
async def create_marketing(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    year: int = Form(...),
    goals: str = Form(...),
    budget: Decimal = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = MarketingPlan(
        code=code,
        title=title,
        year=year,
        goals=goals,
        budget=budget,
        status="draft",
    )
    db.add(item)
    await db.commit()
    return _redirect("/strategic/marketing")


@router.post("/marketing/{plan_id}/edit")
async def edit_marketing(
    request: Request,
    plan_id: int,
    title: str = Form(...),
    goals: str = Form(...),
    budget: Decimal = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(MarketingPlan).where(MarketingPlan.id == plan_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/strategic/marketing")
    item.title = title
    item.goals = goals
    item.budget = budget
    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return _redirect(f"/strategic/marketing/{plan_id}")


@router.post("/marketing/{plan_id}/activate")
async def activate_marketing(
    request: Request,
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(MarketingPlan).where(MarketingPlan.id == plan_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "active"
        await db.commit()
    return _redirect(f"/strategic/marketing/{plan_id}")


@router.post("/marketing/{plan_id}/complete")
async def complete_marketing(
    request: Request,
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(MarketingPlan).where(MarketingPlan.id == plan_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "completed"
        await db.commit()
    return _redirect(f"/strategic/marketing/{plan_id}")


# ─── Strategy Reviews ───────────────────────────────────────────────────


@router.get("/reviews")
async def list_reviews(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(StrategyReview)
    count_stmt = select(func.count()).select_from(StrategyReview.__table__)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(StrategyReview.date.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/strategic/reviews.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "page_title": "Strategy Reviews",
    })


@router.get("/reviews/table")
async def reviews_table(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(StrategyReview)
    count_stmt = select(func.count()).select_from(StrategyReview.__table__)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(StrategyReview.date.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/strategic/_reviews_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    })


@router.get("/reviews/create")
async def create_review_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/strategic/review_create.html", {
        "page_title": "Create Strategy Review",
    })


@router.get("/reviews/{review_id}")
async def detail_review(
    request: Request,
    review_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(StrategyReview).where(StrategyReview.id == review_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/strategic/reviews")
    return render(request, "pages/strategic/review_detail.html", {
        "item": item,
        "page_title": f"Review {item.date}",
    })


@router.post("/reviews")
async def create_review(
    request: Request,
    date_val: date = Form(...),
    reviewed_by: str = Form(...),
    summary: str = Form(...),
    decisions: str = Form(...),
    next_review_date: Optional[date] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = StrategyReview(
        date=date_val,
        reviewed_by=reviewed_by,
        summary=summary,
        decisions=decisions,
        next_review_date=next_review_date,
    )
    db.add(item)
    await db.commit()
    return _redirect("/strategic/reviews")


# ─── Management Review Reports ──────────────────────────────────────────


@router.get("/management-reviews")
async def list_management_reviews(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(ManagementReviewReport)
    count_stmt = select(func.count()).select_from(ManagementReviewReport.__table__)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(ManagementReviewReport.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/strategic/management_reviews.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "page_title": "Management Review Reports",
    })


@router.get("/management-reviews/table")
async def management_reviews_table(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(ManagementReviewReport)
    count_stmt = select(func.count()).select_from(ManagementReviewReport.__table__)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(ManagementReviewReport.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/strategic/_management_reviews_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    })


@router.get("/management-reviews/create")
async def create_management_review_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/strategic/management_review_create.html", {
        "page_title": "Create Management Review Report",
    })


@router.get("/management-reviews/{review_id}")
async def detail_management_review(
    request: Request,
    review_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(
        select(ManagementReviewReport).where(ManagementReviewReport.id == review_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/strategic/management-reviews")
    return render(request, "pages/strategic/management_review_detail.html", {
        "item": item,
        "page_title": f"Management Review {item.code}",
    })


@router.post("/management-reviews")
async def create_management_review(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    review_period_start: date = Form(...),
    review_period_end: date = Form(...),
    prepared_by: str = Form(...),
    summary: str = Form(...),
    conclusions: str = Form(""),
    report_url: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    import json

    conclusions_data = {}
    if conclusions:
        try:
            conclusions_data = json.loads(conclusions)
        except json.JSONDecodeError:
            conclusions_data = {"text": conclusions}

    item = ManagementReviewReport(
        code=code,
        title=title,
        review_period_start=review_period_start,
        review_period_end=review_period_end,
        prepared_by=prepared_by,
        summary=summary,
        conclusions=conclusions_data,
        report_url=report_url or None,
    )
    db.add(item)
    await db.commit()
    return _redirect("/strategic/management-reviews")


# ─── QMS Scope ──────────────────────────────────────────────────────────


@router.get("/scope")
async def show_current_scope(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(
        select(QmsScope).where(QmsScope.is_current == True).order_by(QmsScope.created_at.desc())  # noqa: E712
    )
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/strategic/scope/create")
    return render(request, "pages/strategic/scope_detail.html", {
        "item": item,
        "page_title": "QMS Scope",
    })


@router.get("/scope/create")
async def create_scope_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/strategic/scope_create.html", {
        "page_title": "Create QMS Scope",
    })


@router.get("/scope/history")
async def scope_history(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(QmsScope).order_by(QmsScope.created_at.desc())
    count_stmt = select(func.count()).select_from(QmsScope.__table__)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/strategic/scope_history.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "page_title": "QMS Scope History",
    })


@router.post("/scope")
async def create_scope(
    request: Request,
    version: str = Form("1.0"),
    scope_description: str = Form(...),
    exclusions: str = Form(""),
    applicable_normative: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    # Deactivate previous current scope
    result = await db.execute(
        select(QmsScope).where(QmsScope.is_current == True)  # noqa: E712
    )
    prev = result.scalar_one_or_none()
    if prev:
        prev.is_current = False

    item = QmsScope(
        version=version,
        scope_description=scope_description,
        exclusions=exclusions or None,
        applicable_normative=applicable_normative,
        is_current=True,
    )
    db.add(item)
    await db.commit()
    return _redirect("/strategic/scope")
