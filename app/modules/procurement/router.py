from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.modules.procurement.domain.logic import (
    calculate_supplier_score,
    get_suppliers_due_for_reevaluation,
    get_top_suppliers,
)
from app.modules.procurement.domain.models import (
    EvaluationStatus,
    PurchaseRequest,
    PurchaseRequestStatus,
    ReceivingReport,
    SupplierEvaluation,
    SupplierPerformanceReport,
    SupplierRegister,
    SupplierRegistration,
    SupplierStatus,
)
from app.modules.procurement.schemas.dto import (
    PurchaseRequestCreate,
    PurchaseRequestResponse,
    PurchaseRequestUpdate,
    ReceivingReportCreate,
    ReceivingReportResponse,
    SupplierEvaluationCreate,
    SupplierEvaluationResponse,
    SupplierPerformanceReportCreate,
    SupplierPerformanceReportResponse,
    SupplierRegisterCreate,
    SupplierRegisterResponse,
    SupplierRegisterUpdate,
    SupplierRegistrationCreate,
    SupplierRegistrationResponse,
    SupplierRegistrationUpdate,
)

router = APIRouter()


# ─── Purchase Request (FO-P9-001) ──────────────────────────────────────────

@router.get("/purchase-requests", response_model=List[PurchaseRequestResponse])
async def list_purchase_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    requester: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PurchaseRequest)
    if status_filter:
        stmt = stmt.where(PurchaseRequest.status == status_filter)
    if requester:
        stmt = stmt.where(PurchaseRequest.requester == requester)
    if category:
        stmt = stmt.where(PurchaseRequest.category == category)
    result = await db.execute(stmt.order_by(PurchaseRequest.created_at.desc()))
    return list(result.scalars().all())


@router.post("/purchase-requests", response_model=PurchaseRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_request(payload: PurchaseRequestCreate, db: AsyncSession = Depends(get_db)):
    pr = PurchaseRequest(**payload.model_dump())
    db.add(pr)
    await db.flush()
    return pr


@router.get("/purchase-requests/{pr_id}", response_model=PurchaseRequestResponse)
async def get_purchase_request(pr_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseRequest).where(PurchaseRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    return pr


@router.patch("/purchase-requests/{pr_id}", response_model=PurchaseRequestResponse)
async def update_purchase_request(pr_id: int, payload: PurchaseRequestUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseRequest).where(PurchaseRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pr, field, value)
    await db.flush()
    return pr


@router.post("/purchase-requests/{pr_id}/submit", response_model=PurchaseRequestResponse)
async def submit_purchase_request(pr_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseRequest).where(PurchaseRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    if pr.status != PurchaseRequestStatus.DRAFT.value:
        raise HTTPException(status_code=409, detail="Only draft requests can be submitted")
    pr.status = PurchaseRequestStatus.SUBMITTED.value
    await db.flush()
    return pr


@router.post("/purchase-requests/{pr_id}/approve", response_model=PurchaseRequestResponse)
async def approve_purchase_request(pr_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseRequest).where(PurchaseRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    if pr.status != PurchaseRequestStatus.SUBMITTED.value:
        raise HTTPException(status_code=409, detail="Only submitted requests can be approved")
    pr.status = PurchaseRequestStatus.APPROVED.value
    await db.flush()

    await event_bus.emit(Event(
        name="PurchaseOrderReady",
        payload={
            "purchase_request_id": pr.id,
            "code": pr.code,
            "requester": pr.requester,
            "description": pr.description,
            "estimated_cost": pr.estimated_cost,
            "category": pr.category,
        },
        source_module="procurement",
    ))
    return pr


@router.post("/purchase-requests/{pr_id}/reject", response_model=PurchaseRequestResponse)
async def reject_purchase_request(pr_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseRequest).where(PurchaseRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    if pr.status != PurchaseRequestStatus.SUBMITTED.value:
        raise HTTPException(status_code=409, detail="Only submitted requests can be rejected")
    pr.status = PurchaseRequestStatus.REJECTED.value
    await db.flush()
    return pr


@router.post("/purchase-requests/{pr_id}/order", response_model=PurchaseRequestResponse)
async def order_purchase_request(pr_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseRequest).where(PurchaseRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    if pr.status != PurchaseRequestStatus.APPROVED.value:
        raise HTTPException(status_code=409, detail="Only approved requests can be ordered")
    pr.status = PurchaseRequestStatus.ORDERED.value
    await db.flush()
    return pr


# ─── Supplier Registration (FO-P9-002) ─────────────────────────────────────

@router.get("/suppliers", response_model=List[SupplierRegistrationResponse])
async def list_suppliers(
    status_filter: Optional[str] = Query(None, alias="status"),
    company_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SupplierRegistration)
    if status_filter:
        stmt = stmt.where(SupplierRegistration.status == status_filter)
    if company_name:
        stmt = stmt.where(SupplierRegistration.company_name.ilike(f"%{company_name}%"))
    result = await db.execute(stmt.order_by(SupplierRegistration.created_at.desc()))
    return list(result.scalars().all())


@router.post("/suppliers", response_model=SupplierRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(payload: SupplierRegistrationCreate, db: AsyncSession = Depends(get_db)):
    supplier = SupplierRegistration(**payload.model_dump())
    db.add(supplier)
    await db.flush()
    return supplier


@router.get("/suppliers/{supplier_id}", response_model=SupplierRegistrationResponse)
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplierRegistration).where(SupplierRegistration.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierRegistrationResponse)
async def update_supplier(supplier_id: int, payload: SupplierRegistrationUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplierRegistration).where(SupplierRegistration.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    await db.flush()
    return supplier


@router.post("/suppliers/{supplier_id}/approve", response_model=SupplierRegistrationResponse)
async def approve_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplierRegistration).where(SupplierRegistration.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if supplier.status != SupplierStatus.PENDING.value:
        raise HTTPException(status_code=409, detail="Only pending suppliers can be approved")
    supplier.status = SupplierStatus.APPROVED.value
    await db.flush()
    return supplier


@router.post("/suppliers/{supplier_id}/reject", response_model=SupplierRegistrationResponse)
async def reject_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplierRegistration).where(SupplierRegistration.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if supplier.status != SupplierStatus.PENDING.value:
        raise HTTPException(status_code=409, detail="Only pending suppliers can be rejected")
    supplier.status = SupplierStatus.REJECTED.value
    await db.flush()
    return supplier


# ─── Supplier Evaluation (FO-P9-003) ───────────────────────────────────────

@router.get("/evaluations", response_model=List[SupplierEvaluationResponse])
async def list_evaluations(
    supplier_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SupplierEvaluation)
    if supplier_id is not None:
        stmt = stmt.where(SupplierEvaluation.supplier_id == supplier_id)
    if status_filter:
        stmt = stmt.where(SupplierEvaluation.status == status_filter)
    result = await db.execute(stmt.order_by(SupplierEvaluation.created_at.desc()))
    return list(result.scalars().all())


@router.post("/evaluations", response_model=SupplierEvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(payload: SupplierEvaluationCreate, db: AsyncSession = Depends(get_db)):
    # Verify supplier exists
    sup_result = await db.execute(
        select(SupplierRegistration).where(SupplierRegistration.id == payload.supplier_id)
    )
    if not sup_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Supplier not found")

    evaluation = SupplierEvaluation(
        supplier_id=payload.supplier_id,
        evaluator=payload.evaluator,
        criteria_scores=payload.criteria_scores.model_dump(),
        period=payload.period,
        status=EvaluationStatus.DRAFT,
    )
    db.add(evaluation)
    await db.flush()
    return evaluation


@router.get("/evaluations/{eval_id}", response_model=SupplierEvaluationResponse)
async def get_evaluation(eval_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplierEvaluation).where(SupplierEvaluation.id == eval_id))
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.post("/evaluations/{eval_id}/complete", response_model=SupplierEvaluationResponse)
async def complete_evaluation(eval_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplierEvaluation).where(SupplierEvaluation.id == eval_id))
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    if evaluation.status != EvaluationStatus.DRAFT.value:
        raise HTTPException(status_code=409, detail="Only draft evaluations can be completed")

    # Calculate and persist the total score
    evaluation.total_score = calculate_supplier_score(evaluation)
    evaluation.status = EvaluationStatus.COMPLETED
    await db.flush()

    await event_bus.emit(Event(
        name="SupplierEvaluated",
        payload={
            "evaluation_id": evaluation.id,
            "supplier_id": evaluation.supplier_id,
            "total_score": evaluation.total_score,
            "period": evaluation.period,
            "evaluator": evaluation.evaluator,
        },
        source_module="procurement",
    ))
    return evaluation


# ─── Supplier Performance Report (INF-P9-001) ──────────────────────────────

@router.get("/performance-reports", response_model=List[SupplierPerformanceReportResponse])
async def list_performance_reports(
    supplier_id: Optional[int] = None,
    period: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SupplierPerformanceReport)
    if supplier_id is not None:
        stmt = stmt.where(SupplierPerformanceReport.supplier_id == supplier_id)
    if period:
        stmt = stmt.where(SupplierPerformanceReport.period == period)
    result = await db.execute(stmt.order_by(SupplierPerformanceReport.created_at.desc()))
    return list(result.scalars().all())


@router.post(
    "/performance-reports",
    response_model=SupplierPerformanceReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_report(
    payload: SupplierPerformanceReportCreate,
    db: AsyncSession = Depends(get_db),
):
    sup_result = await db.execute(
        select(SupplierRegistration).where(SupplierRegistration.id == payload.supplier_id)
    )
    if not sup_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Supplier not found")

    report = SupplierPerformanceReport(**payload.model_dump())
    db.add(report)
    await db.flush()
    return report


@router.get("/performance-reports/{report_id}", response_model=SupplierPerformanceReportResponse)
async def get_performance_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SupplierPerformanceReport).where(SupplierPerformanceReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Performance report not found")
    return report


# ─── Receiving Report (FO-P9-004) ──────────────────────────────────────────

@router.get("/receiving-reports", response_model=List[ReceivingReportResponse])
async def list_receiving_reports(
    purchase_request_id: Optional[int] = None,
    condition_ok: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ReceivingReport)
    if purchase_request_id is not None:
        stmt = stmt.where(ReceivingReport.purchase_request_id == purchase_request_id)
    if condition_ok is not None:
        stmt = stmt.where(ReceivingReport.condition_ok == condition_ok)
    result = await db.execute(stmt.order_by(ReceivingReport.received_date.desc()))
    return list(result.scalars().all())


@router.post("/receiving-reports", response_model=ReceivingReportResponse, status_code=status.HTTP_201_CREATED)
async def create_receiving_report(payload: ReceivingReportCreate, db: AsyncSession = Depends(get_db)):
    if payload.purchase_request_id is not None:
        pr_result = await db.execute(
            select(PurchaseRequest).where(PurchaseRequest.id == payload.purchase_request_id)
        )
        if not pr_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Purchase request not found")

    report = ReceivingReport(**payload.model_dump())
    db.add(report)
    await db.flush()
    return report


@router.get("/receiving-reports/{report_id}", response_model=ReceivingReportResponse)
async def get_receiving_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReceivingReport).where(ReceivingReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Receiving report not found")
    return report


# ─── Supplier Register (REG-P9-001) ────────────────────────────────────────

@router.get("/register", response_model=List[SupplierRegisterResponse])
async def list_supplier_register(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SupplierRegister)
    if category:
        stmt = stmt.where(SupplierRegister.category == category)
    if is_active is not None:
        stmt = stmt.where(SupplierRegister.is_active == is_active)
    result = await db.execute(stmt.order_by(SupplierRegister.approved_at.desc()))
    return list(result.scalars().all())


@router.post("/register", response_model=SupplierRegisterResponse, status_code=status.HTTP_201_CREATED)
async def create_register_entry(payload: SupplierRegisterCreate, db: AsyncSession = Depends(get_db)):
    # Verify supplier exists and is approved
    sup_result = await db.execute(
        select(SupplierRegistration).where(SupplierRegistration.id == payload.supplier_id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if supplier.status != SupplierStatus.APPROVED.value:
        raise HTTPException(status_code=409, detail="Only approved suppliers can be registered")

    # Check for duplicate register entry
    existing = await db.execute(
        select(SupplierRegister).where(SupplierRegister.supplier_id == payload.supplier_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Supplier already registered")

    entry = SupplierRegister(
        supplier_id=payload.supplier_id,
        approved_by=payload.approved_by,
        approved_at=datetime.now(timezone.utc),
        category=payload.category,
    )
    db.add(entry)
    await db.flush()
    return entry


@router.get("/register/{entry_id}", response_model=SupplierRegisterResponse)
async def get_register_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplierRegister).where(SupplierRegister.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Register entry not found")
    return entry


@router.patch("/register/{entry_id}", response_model=SupplierRegisterResponse)
async def update_register_entry(
    entry_id: int,
    payload: SupplierRegisterUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SupplierRegister).where(SupplierRegister.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Register entry not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    await db.flush()
    return entry


# ─── Business Logic Endpoints ──────────────────────────────────────────────

@router.get("/top-suppliers", response_model=List[SupplierRegistrationResponse])
async def top_suppliers(
    category: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Return best-performing approved suppliers, optionally by category."""
    return await get_top_suppliers(db, category=category, limit=limit)


@router.get("/suppliers/due-for-reevaluation", response_model=List[SupplierRegistrationResponse])
async def suppliers_due_for_reevaluation(db: AsyncSession = Depends(get_db)):
    """Return approved suppliers that have no completed evaluation."""
    return await get_suppliers_due_for_reevaluation(db)
