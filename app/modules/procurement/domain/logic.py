"""Business logic for P9 — Procurement & Supplier Management."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.procurement.domain.models import (
    EvaluationStatus,
    SupplierEvaluation,
    SupplierPerformanceReport,
    SupplierRegister,
    SupplierRegistration,
    SupplierStatus,
)


# ─── Supplier Score ─────────────────────────────────────────────────────

def calculate_supplier_score(evaluation: SupplierEvaluation) -> float:
    """Weighted average of criteria_scores mapped to 0–100.

    Weights: quality=0.30, price=0.25, delivery=0.25, service=0.20
    Each criterion is 1–5 → normalised to 0–100 then weighted.
    """
    weights = {"quality": 0.30, "price": 0.25, "delivery": 0.25, "service": 0.20}
    scores = evaluation.criteria_scores
    total = 0.0
    for criterion, weight in weights.items():
        raw = scores.get(criterion, 1)
        # Normalise 1–5 → 0–100: ((raw - 1) / 4) * 100
        normalised = ((raw - 1) / 4) * 100
        total += normalised * weight
    return round(total, 2)


# ─── Top Suppliers ──────────────────────────────────────────────────────

async def get_top_suppliers(
    db: AsyncSession,
    category: Optional[str] = None,
    limit: int = 10,
) -> List[SupplierRegistration]:
    """Return best-performing approved suppliers, optionally filtered by category.

    Ordered by most recent performance report avg_score descending. Suppliers
    without a performance report are excluded.
    """
    # Subquery: latest performance report per supplier
    latest_report = (
        select(
            SupplierPerformanceReport.supplier_id,
            func.max(SupplierPerformanceReport.created_at).label("max_created"),
        )
        .group_by(SupplierPerformanceReport.supplier_id)
        .subquery()
    )

    stmt = (
        select(SupplierRegistration)
        .join(SupplierRegister, SupplierRegistration.id == SupplierRegister.supplier_id)
        .join(
            SupplierPerformanceReport,
            SupplierRegistration.id == SupplierPerformanceReport.supplier_id,
        )
        .join(
            latest_report,
            and_(
                SupplierPerformanceReport.supplier_id == latest_report.c.supplier_id,
                SupplierPerformanceReport.created_at == latest_report.c.max_created,
            ),
        )
        .where(SupplierRegistration.status == SupplierStatus.APPROVED)
        .where(SupplierRegister.is_active.is_(True))
        .order_by(SupplierPerformanceReport.avg_score.desc())
        .limit(limit)
    )

    if category:
        stmt = stmt.where(SupplierRegister.category == category)

    result = await db.execute(stmt)
    return list(result.scalars().all())


# ─── Suppliers Due for Re-evaluation ────────────────────────────────────

async def get_suppliers_due_for_reevaluation(
    db: AsyncSession,
) -> List[SupplierRegistration]:
    """Return approved suppliers that have no evaluation in the current period.

    A supplier is "due for re-evaluation" when there is no completed evaluation
    whose period matches the most recent completed evaluation's period for any
    supplier — i.e., suppliers that haven't been evaluated yet or whose latest
    evaluation is not in the current active period.

    For simplicity, this returns approved suppliers with no completed evaluation
    at all. The caller can refine the period logic.
    """
    # Subquery: suppliers that have at least one completed evaluation
    evaluated_subq = (
        select(SupplierEvaluation.supplier_id)
        .where(SupplierEvaluation.status == EvaluationStatus.COMPLETED)
        .distinct()
        .subquery()
    )

    stmt = (
        select(SupplierRegistration)
        .join(SupplierRegister, SupplierRegistration.id == SupplierRegister.supplier_id)
        .outerjoin(evaluated_subq, SupplierRegistration.id == evaluated_subq.c.supplier_id)
        .where(SupplierRegistration.status == SupplierStatus.APPROVED)
        .where(SupplierRegister.is_active.is_(True))
        .where(evaluated_subq.c.supplier_id.is_(None))
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())
