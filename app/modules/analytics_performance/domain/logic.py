"""Business logic for P11 — Data Analysis & Performance Evaluation."""

from __future__ import annotations

import math
from typing import Any, Optional

from app.modules.analytics_performance.domain.models import (
    IndicatorStatus,
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
