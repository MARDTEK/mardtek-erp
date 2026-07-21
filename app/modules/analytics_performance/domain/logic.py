"""Business logic for P11 — Data Analysis & Performance Evaluation."""

from __future__ import annotations

import math
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics_performance.domain.models import (
    IndicatorStatus,
    PerformanceDataRecord,
    PerformanceDashboard,
    PerformanceIndicator,
    TrendDirection,
)


# ─── Indicator Status ────────────────────────────────────────────────────

def calculate_indicator_status(value: float, target: Optional[float]) -> str:
    """Determine KPI status based on actual value vs target.

    Returns one of: achieved, on_track, at_risk, critical.
    """
    if target is None:
        return IndicatorStatus.ON_TRACK.value

    if target == 0:
        return IndicatorStatus.ON_TRACK.value if value == 0 else IndicatorStatus.CRITICAL.value

    ratio = value / target

    if ratio >= 1.0:
        return IndicatorStatus.ACHIEVED.value
    if ratio >= 0.9:
        return IndicatorStatus.ON_TRACK.value
    if ratio >= 0.75:
        return IndicatorStatus.AT_RISK.value
    return IndicatorStatus.CRITICAL.value


# ─── Trend Analysis ──────────────────────────────────────────────────────

def generate_trend(
    indicator_id: int,
    data_points: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate trend analysis from a sorted list of data points.

    Each data point dict must have ``period`` (str) and ``value`` (float).
    Returns slope, direction, volatility, and change percent.
    """
    if not data_points:
        return {
            "indicator_id": indicator_id,
            "direction": TrendDirection.FLAT.value,
            "slope": 0.0,
            "volatility": 0.0,
            "change_percent": 0.0,
        }

    values = [dp["value"] for dp in data_points]
    n = len(values)

    # Simple linear regression for slope
    if n < 2:
        return {
            "indicator_id": indicator_id,
            "direction": TrendDirection.FLAT.value,
            "slope": 0.0,
            "volatility": 0.0,
            "change_percent": 0.0,
        }

    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
    denominator = sum((xi - x_mean) ** 2 for xi in x)

    slope = numerator / denominator if denominator != 0 else 0.0

    # Direction
    if abs(slope) < 0.001:
        direction = TrendDirection.FLAT.value
    elif slope > 0:
        direction = TrendDirection.UP.value
    else:
        direction = TrendDirection.DOWN.value

    # Volatility: coefficient of variation
    mean = y_mean
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0.0
    volatility = std / mean if mean != 0 else 0.0

    if volatility > 0.5:
        direction = TrendDirection.VOLATILE.value

    # Change percent: first to last
    change_percent = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0.0

    return {
        "indicator_id": indicator_id,
        "direction": direction,
        "slope": round(slope, 4),
        "volatility": round(volatility, 4),
        "change_percent": round(change_percent, 2),
    }


# ─── Dashboard KPI Aggregation ───────────────────────────────────────────

async def get_dashboard_kpis(
    db: AsyncSession,
    dashboard_id: int,
) -> list[dict[str, Any]]:
    """Aggregate KPI values for a given dashboard's indicators."""
    result = await db.execute(
        select(PerformanceDashboard).where(PerformanceDashboard.id == dashboard_id)
    )
    dashboard = result.scalar_one_or_none()
    if dashboard is None:
        return []

    # Get all active indicators (or filter by layout-defined ones)
    indicators_result = await db.execute(
        select(PerformanceIndicator).where(PerformanceIndicator.is_active.is_(True))
    )
    indicators = list(indicators_result.scalars().all())

    aggregated: list[dict[str, Any]] = []
    for ind in indicators:
        # Get the latest data record for this indicator
        record_result = await db.execute(
            select(PerformanceDataRecord)
            .where(PerformanceDataRecord.indicator_id == ind.id)
            .order_by(PerformanceDataRecord.recorded_at.desc())
            .limit(1)
        )
        record = record_result.scalar_one_or_none()

        aggregated.append({
            "indicator_id": ind.id,
            "code": ind.code,
            "name": ind.name,
            "process_code": ind.process_code,
            "target": ind.target_value,
            "unit": ind.unit,
            "latest_value": record.value if record else None,
            "latest_period": record.period if record else None,
            "status": calculate_indicator_status(record.value, ind.target_value) if record else "no_data",
        })

    return aggregated


# ─── Process KPI Consolidation ───────────────────────────────────────────

async def consolidate_process_kpis(
    db: AsyncSession,
    process_code: str,
    period: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Consolidate all KPIs for a given process code with their latest data points."""
    stmt = select(PerformanceIndicator).where(
        PerformanceIndicator.process_code == process_code,
        PerformanceIndicator.is_active.is_(True),
    )
    result = await db.execute(stmt)
    indicators = list(result.scalars().all())

    consolidated: list[dict[str, Any]] = []
    for ind in indicators:
        record_stmt = select(PerformanceDataRecord).where(
            PerformanceDataRecord.indicator_id == ind.id,
        )
        if period:
            record_stmt = record_stmt.where(PerformanceDataRecord.period == period)

        record_stmt = record_stmt.order_by(PerformanceDataRecord.recorded_at.desc()).limit(1)
        record_result = await db.execute(record_stmt)
        record = record_result.scalar_one_or_none()

        consolidated.append({
            "indicator_id": ind.id,
            "code": ind.code,
            "name": ind.name,
            "formula": ind.formula,
            "target": ind.target_value,
            "unit": ind.unit,
            "latest_value": record.value if record else None,
            "latest_period": record.period if record else None,
            "status": calculate_indicator_status(record.value, ind.target_value) if record else "no_data",
        })

    return consolidated
