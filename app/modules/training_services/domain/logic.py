"""Business logic for P6 — Training & Human Development."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.training_services.domain.models import (
    CertificationRecord,
    CompetencyMatrix,
    SessionStatus,
    TrainingEvaluation,
    TrainingSession,
)


async def calculate_training_effectiveness(
    db: AsyncSession, course_id: int
) -> dict[str, Any]:
    """Calculate average evaluation score and completion rate for a course.

    Returns a dict with ``avg_score``, ``completion_rate``, ``total_sessions``,
    and ``total_attendees``.
    """
    # Count sessions for this course
    session_result = await db.execute(
        select(TrainingSession).where(TrainingSession.course_id == course_id)
    )
    sessions = list(session_result.scalars().all())
    total_sessions = len(sessions)
    completed_sessions = [s for s in sessions if s.status == SessionStatus.COMPLETED]

    # Average evaluation score across all sessions
    score_result = await db.execute(
        select(func.avg(TrainingEvaluation.score)).where(
            TrainingEvaluation.session_id.in_([s.id for s in sessions])
        )
    )
    avg_score = score_result.scalar() or 0.0

    # Total unique attendees (flattened from session attendees JSON)
    total_attendees = len(
        {
            attendee
            for s in sessions
            for attendee in (s.attendees or [])
        }
    )

    completion_rate = (
        round(len(completed_sessions) / total_sessions, 4) if total_sessions > 0 else 0.0
    )

    return {
        "course_id": course_id,
        "avg_score": round(float(avg_score), 2),
        "completion_rate": completion_rate,
        "total_sessions": total_sessions,
        "completed_sessions": len(completed_sessions),
        "total_attendees": total_attendees,
    }


async def update_competency_gap(
    db: AsyncSession,
    matrix_id: int,
    role: str,
    competencies: List[Dict[str, Any]],
) -> Optional[CompetencyMatrix]:
    """Update a competency matrix with new competencies and recalculate gaps.

    Each competency dict must contain at least ``name``, ``required_level``,
    and ``current_level``. The ``gap`` is computed as
    ``required_level - current_level``.
    """
    result = await db.execute(
        select(CompetencyMatrix).where(CompetencyMatrix.id == matrix_id)
    )
    matrix = result.scalar_one_or_none()
    if matrix is None:
        return None

    enriched: list[dict[str, Any]] = []
    for comp in competencies:
        enriched.append({
            "name": comp["name"],
            "required_level": comp["required_level"],
            "current_level": comp["current_level"],
            "gap": max(0, comp["required_level"] - comp["current_level"]),
        })

    matrix.role = role
    matrix.competencies = enriched
    await db.flush()
    return matrix


async def get_certifications_by_participant(
    db: AsyncSession, name: str
) -> list[CertificationRecord]:
    """Retrieve all certification records for a given participant by exact name match."""
    result = await db.execute(
        select(CertificationRecord)
        .where(CertificationRecord.participant_name == name)
        .order_by(CertificationRecord.issued_at.desc())
    )
    return list(result.scalars().all())
