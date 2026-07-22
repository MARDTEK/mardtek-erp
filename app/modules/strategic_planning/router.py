from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.modules.strategic_planning.domain.logic import (
    calculate_objective_progress,
    create_management_review_report,
    get_active_qms_scope,
    get_objectives_by_process,
)
from app.modules.strategic_planning.domain.models import (
    ManagementReviewReport,
    MarketingPlan,
    MarketingPlanStatus,
    ObjectiveStatus,
    PolicyStatus,
    QmsScope,
    QualityObjective,
    QualityPolicy,
    StrategyReview,
)
from app.modules.strategic_planning.schemas.dto import (
    ManagementReviewCreate,
    ManagementReviewResponse,
    MarketingPlanCreate,
    MarketingPlanResponse,
    MarketingPlanUpdate,
    QualityObjectiveCreate,
    QualityObjectiveResponse,
    QualityObjectiveUpdateProgress,
    QualityPolicyApprove,
    QualityPolicyCreate,
    QualityPolicyResponse,
    QualityPolicyUpdate,
    QmsScopeCreate,
    QmsScopeResponse,
    QmsScopeUpdate,
    StrategyReviewCreate,
    StrategyReviewResponse,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# ─── Quality Policies ──────────────────────────────────────────────────

@router.get("/quality-policies", response_model=List[QualityPolicyResponse])
async def list_quality_policies(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(QualityPolicy)
    if status_filter:
        stmt = stmt.where(QualityPolicy.status == status_filter)
    result = await db.execute(stmt.order_by(QualityPolicy.code))
    return list(result.scalars().all())


@router.post("/quality-policies", response_model=QualityPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_quality_policy(payload: QualityPolicyCreate, db: AsyncSession = Depends(get_db)):
    policy = QualityPolicy(**payload.model_dump())
    db.add(policy)
    await db.flush()
    return policy


@router.get("/quality-policies/{policy_id}", response_model=QualityPolicyResponse)
async def get_quality_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QualityPolicy).where(QualityPolicy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Quality policy not found")
    return policy


@router.post("/quality-policies/{policy_id}/approve", response_model=QualityPolicyResponse)
async def approve_quality_policy(
    policy_id: int,
    payload: QualityPolicyApprove,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QualityPolicy).where(QualityPolicy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Quality policy not found")
    policy.status = PolicyStatus.APPROVED
    policy.approved_by = payload.approved_by
    policy.approved_at = datetime.now(timezone.utc)
    await db.flush()
    return policy


# ─── Quality Objectives ─────────────────────────────────────────────────

@router.get("/quality-objectives", response_model=List[QualityObjectiveResponse])
async def list_quality_objectives(
    year: int | None = None,
    process_code: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(QualityObjective)
    if year:
        stmt = stmt.where(QualityObjective.year == year)
    if process_code:
        stmt = stmt.where(QualityObjective.process_code == process_code)
    if status_filter:
        stmt = stmt.where(QualityObjective.status == status_filter)
    result = await db.execute(stmt.order_by(QualityObjective.code))
    return list(result.scalars().all())


@router.post("/quality-objectives", response_model=QualityObjectiveResponse, status_code=status.HTTP_201_CREATED)
async def create_quality_objective(payload: QualityObjectiveCreate, db: AsyncSession = Depends(get_db)):
    obj = QualityObjective(**payload.model_dump())
    db.add(obj)
    await db.flush()
    return obj


@router.get("/quality-objectives/{objective_id}", response_model=QualityObjectiveResponse)
async def get_quality_objective(objective_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QualityObjective).where(QualityObjective.id == objective_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Quality objective not found")
    return obj


@router.patch("/quality-objectives/{objective_id}/progress", response_model=QualityObjectiveResponse)
async def update_objective_progress(
    objective_id: int,
    payload: QualityObjectiveUpdateProgress,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QualityObjective).where(QualityObjective.id == objective_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Quality objective not found")

    obj.actual_value = payload.actual_value
    progress = calculate_objective_progress(obj)

    # Auto-set status based on progress
    if progress >= 100.0:
        obj.status = ObjectiveStatus.ACHIEVED
    elif progress >= 75.0:
        obj.status = ObjectiveStatus.ON_TRACK
    elif progress >= 50.0:
        obj.status = ObjectiveStatus.AT_RISK
    else:
        obj.status = ObjectiveStatus.BEHIND

    await db.flush()
    return obj


# ─── Marketing Plans ─────────────────────────────────────────────────────

@router.get("/marketing-plans", response_model=List[MarketingPlanResponse])
async def list_marketing_plans(
    year: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MarketingPlan)
    if year:
        stmt = stmt.where(MarketingPlan.year == year)
    if status_filter:
        stmt = stmt.where(MarketingPlan.status == status_filter)
    result = await db.execute(stmt.order_by(MarketingPlan.year.desc(), MarketingPlan.code))
    return list(result.scalars().all())


@router.post("/marketing-plans", response_model=MarketingPlanResponse, status_code=status.HTTP_201_CREATED)
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


@router.patch("/marketing-plans/{plan_id}", response_model=MarketingPlanResponse)
async def update_marketing_plan(
    plan_id: int,
    payload: MarketingPlanUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MarketingPlan).where(MarketingPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Marketing plan not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.flush()
    return plan


# ─── Strategy Reviews ───────────────────────────────────────────────────

@router.post("/strategy-reviews", response_model=StrategyReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy_review(payload: StrategyReviewCreate, db: AsyncSession = Depends(get_db)):
    review = StrategyReview(**payload.model_dump())
    db.add(review)
    await db.flush()
    return review


@router.get("/strategy-reviews", response_model=List[StrategyReviewResponse])
async def list_strategy_reviews(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StrategyReview).order_by(StrategyReview.date.desc())
    )
    return list(result.scalars().all())


# ─── Management Review Reports ──────────────────────────────────────────

@router.post("/management-reviews", response_model=ManagementReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_management_review(
    payload: ManagementReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    report = await create_management_review_report(
        db=db,
        code=payload.code,
        title=payload.title,
        review_period_start=payload.review_period_start,
        review_period_end=payload.review_period_end,
        prepared_by=payload.prepared_by,
        summary=payload.summary,
        conclusions=payload.conclusions,
        report_url=payload.report_url,
    )

    # Emit event so other modules can react (e.g. P2 — Quality Management)
    await event_bus.emit(
        Event(
            name="ManagementReviewCompleted",
            payload={
                "report_id": report.id,
                "code": report.code,
                "title": report.title,
                "review_period_start": str(report.review_period_start),
                "review_period_end": str(report.review_period_end),
                "prepared_by": report.prepared_by,
            },
            source_module="strategic_planning",
        )
    )

    return report


@router.get("/management-reviews", response_model=List[ManagementReviewResponse])
async def list_management_reviews(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ManagementReviewReport).order_by(ManagementReviewReport.created_at.desc())
    )
    return list(result.scalars().all())


# ─── QMS Scope ──────────────────────────────────────────────────────────

@router.get("/qms-scope", response_model=QmsScopeResponse)
async def get_current_qms_scope(db: AsyncSession = Depends(get_db)):
    scope = await get_active_qms_scope(db)
    if not scope:
        raise HTTPException(status_code=404, detail="No active QMS scope found")
    return scope


@router.post("/qms-scope", response_model=QmsScopeResponse, status_code=status.HTTP_201_CREATED)
async def create_qms_scope(payload: QmsScopeCreate, db: AsyncSession = Depends(get_db)):
    # Deactivate any existing current scope
    existing = await get_active_qms_scope(db)
    if existing:
        existing.is_current = False

    scope = QmsScope(**payload.model_dump(), is_current=True)
    db.add(scope)
    await db.flush()
    return scope


@router.patch("/qms-scope/{scope_id}", response_model=QmsScopeResponse)
async def update_qms_scope(
    scope_id: int,
    payload: QmsScopeUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QmsScope).where(QmsScope.id == scope_id))
    scope = result.scalar_one_or_none()
    if not scope:
        raise HTTPException(status_code=404, detail="QMS scope not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(scope, field, value)
    await db.flush()
    return scope
