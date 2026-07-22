"""Business logic for P8 — Infrastructure & Technology."""

from __future__ import annotations

from typing import Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.infrastructure_it.domain.models import (
    IncidentReport,
    IncidentSeverity,
    IncidentStatus,
)


# ─── SLA Compliance ──────────────────────────────────────────────────────

def check_sla_compliance(uptime_percent: float, sla_target: float) -> bool:
    """Compare actual uptime against the SLA target.

    Args:
        uptime_percent: Measured uptime percentage (e.g. 99.95).
        sla_target: Contractual SLA target (e.g. 99.9).

    Returns:
        ``True`` if uptime meets or exceeds the target.
    """
    return uptime_percent >= sla_target


# ─── Uptime Calculation ───────────────────────────────────────────────────

def calculate_uptime(downtime_minutes: int, period_minutes: int) -> float:
    """Calculate uptime percentage from total downtime in a given period.

    Args:
        downtime_minutes: Total minutes the service was unavailable.
        period_minutes: Total minutes in the measurement period.

    Returns:
        Uptime percentage rounded to two decimal places (e.g. 99.95).
    """
    if period_minutes <= 0:
        return 100.0
    uptime = ((period_minutes - downtime_minutes) / period_minutes) * 100.0
    return round(max(uptime, 0.0), 2)


# ─── Incident Queries ─────────────────────────────────────────────────────

async def get_open_incidents_by_severity(db: AsyncSession) -> Dict[str, int]:
    """Return a count of open (non-closed) incidents grouped by severity.

    Returns:
        A dict mapping severity level (P1, P2, P3, P4) to count.
    """
    result = await db.execute(
        select(IncidentReport.severity, func.count(IncidentReport.id))
        .where(IncidentReport.status != IncidentStatus.CLOSED)
        .group_by(IncidentReport.severity)
    )
    return {row[0].value: row[1] for row in result.all()}
