"""Business logic for P10 — Customer Satisfaction."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.customer_experience.domain.models import (
    ComplaintClaim,
    ComplaintStatus,
    NpsCategory,
    NpsSurvey,
)


# ─── NPS ─────────────────────────────────────────────────────────────────

def auto_categorize_nps(score: int) -> str:
    """Classify an NPS score into promoter (9-10), passive (7-8), or detractor (0-6).

    Per the standard Net Promoter Score methodology.
    """
    if score >= 9:
        return NpsCategory.PROMOTER.value
    if score >= 7:
        return NpsCategory.PASSIVE.value
    return NpsCategory.DETRACTOR.value


def calculate_nps(scores: list[int]) -> int:
    """Calculate NPS = %Promoters - %Detractors, rounded to integer.

    Returns an integer between -100 and 100. Returns 0 for empty lists.
    """
    if not scores:
        return 0
    total = len(scores)
    promoters = sum(1 for s in scores if s >= 9)
    detractors = sum(1 for s in scores if s <= 6)
    return round((promoters / total) * 100 - (detractors / total) * 100)


# ─── CSAT ────────────────────────────────────────────────────────────────

def calculate_csat(scores: list[int]) -> float:
    """Calculate CSAT = average score (1-5 scale), rounded to 2 decimals.

    Returns 0.0 for empty lists.
    """
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


# ─── CES ─────────────────────────────────────────────────────────────────

def calculate_ces(scores: list[int]) -> float:
    """Calculate CES = average score (1-7 scale), rounded to 2 decimals.

    Returns 0.0 for empty lists.
    """
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


# ─── Complaints ──────────────────────────────────────────────────────────

async def get_complaints_by_status(
    db: AsyncSession,
    status: ComplaintStatus | str,
) -> list[ComplaintClaim]:
    """Retrieve complaints filtered by status."""
    result = await db.execute(
        select(ComplaintClaim)
        .where(ComplaintClaim.status == status)
        .order_by(ComplaintClaim.created_at.desc())
    )
    return list(result.scalars().all())


async def get_nps_average(db: AsyncSession) -> Optional[float]:
    """Calculate the average NPS score across all surveys."""
    result = await db.execute(select(func.avg(NpsSurvey.score)))
    avg = result.scalar()
    return round(float(avg), 2) if avg is not None else None
