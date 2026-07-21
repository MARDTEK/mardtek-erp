"""Business logic for P5 — Project Implementation & Execution."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pmo_projects.domain.models import (
    CRStatus,
    ChecklistStatus,
    ClosureStatus,
    DeliverablesChecklist,
    HandoverStatus,
    Project,
    ProjectClosureRecord,
    ProjectExecutionPlan,
    ProjectStatus,
)


# ─── Project Progress ────────────────────────────────────────────────────

async def calculate_project_progress(project_id: int, db: AsyncSession) -> Dict[str, Any]:
    """Calculate project completion percentage based on deliverables checklist.

    Returns a dict with total items, completed count, and percentage.
    Returns zeroed stats if no checklist exists.
    """
    result = await db.execute(
        select(DeliverablesChecklist).where(DeliverablesChecklist.project_id == project_id)
    )
    checklist = result.scalar_one_or_none()

    if checklist is None or not checklist.items:
        return {"total": 0, "completed": 0, "percentage": 0.0}

    items = list(checklist.items)
    total = len(items)
    completed = sum(1 for item in items if item.get("completed_at"))
    percentage = round((completed / total) * 100, 2) if total > 0 else 0.0

    return {
        "total": total,
        "completed": completed,
        "percentage": percentage,
    }


# ─── Project Closure ─────────────────────────────────────────────────────

async def close_project(
    db: AsyncSession,
    project_id: int,
    lessons_learned: Optional[str] = None,
    final_budget: Optional[Decimal] = None,
    customer_feedback: Optional[str] = None,
) -> Optional[ProjectClosureRecord]:
    """Close a project after verifying all deliverables are done.

    Validates:
    - All deliverables are completed
    - No open/active change requests remain

    Returns the created ProjectClosureRecord, or None if preconditions fail.
    """
    # Fetch project
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if project is None:
        return None

    # Verify deliverables are all complete
    checklist_result = await db.execute(
        select(DeliverablesChecklist).where(DeliverablesChecklist.project_id == project_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    if checklist is not None:
        items = list(checklist.items) if checklist.items else []
        incomplete = [item for item in items if not item.get("completed_at")]
        if incomplete:
            return None  # Cannot close — pending deliverables

    # Verify no open change requests
    from app.modules.pmo_projects.domain.models import ChangeRequest
    cr_result = await db.execute(
        select(ChangeRequest).where(
            ChangeRequest.project_id == project_id,
            ChangeRequest.status == CRStatus.SUBMITTED,
        )
    )
    open_crs = list(cr_result.scalars().all())
    if open_crs:
        return None  # Cannot close — open change requests

    # Update project status
    project.status = ProjectStatus.CLOSED
    project.end_date = datetime.now(timezone.utc).date()

    # Update checklist status if exists
    if checklist is not None:
        checklist.status = ChecklistStatus.COMPLETED

    # Create closure record
    closure = ProjectClosureRecord(
        project_id=project_id,
        lessons_learned=lessons_learned,
        final_budget=final_budget,
        customer_feedback=customer_feedback,
        status=ClosureStatus.CLOSED,
    )
    db.add(closure)
    await db.flush()
    return closure


# ─── Overdue Change Requests ─────────────────────────────────────────────

async def get_overdue_change_requests(
    db: AsyncSession, project_id: int
) -> List[dict]:
    """Return change requests that are still submitted (pending approval/rejection)."""
    from app.modules.pmo_projects.domain.models import ChangeRequest

    result = await db.execute(
        select(ChangeRequest).where(
            ChangeRequest.project_id == project_id,
            ChangeRequest.status == CRStatus.SUBMITTED,
        ).order_by(ChangeRequest.created_at.asc())
    )
    crs = list(result.scalars().all())
    return [
        {
            "id": cr.id,
            "code": cr.code,
            "description": cr.description,
            "reason": cr.reason,
            "requested_by": cr.requested_by,
            "created_at": cr.created_at,
            "days_open": (datetime.now(timezone.utc) - cr.created_at).days,
        }
        for cr in crs
    ]


# ─── Milestone-Driven Status Update ──────────────────────────────────────

async def update_project_status_from_milestones(
    db: AsyncSession, project_id: int
) -> str:
    """Auto-update project status based on execution plan milestones.

    Rules:
    - No execution plan → keep current status.
    - At least one milestone completed → in_execution.
    - All milestones completed → closed (creates closure record if needed).
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        return "not_found"

    plan_result = await db.execute(
        select(ProjectExecutionPlan).where(ProjectExecutionPlan.project_id == project_id)
    )
    plan = plan_result.scalar_one_or_none()
    if plan is None or not plan.milestones:
        return project.status.value  # No plan to evaluate against

    milestones = list(plan.milestones)
    total = len(milestones)
    completed = sum(1 for m in milestones if m.get("completed_at"))
    any_started = any(m.get("completed_at") for m in milestones)

    if completed == total and total > 0:
        # All milestones done — close the project
        if project.status != ProjectStatus.CLOSED:
            project.status = ProjectStatus.CLOSED
            project.end_date = datetime.now(timezone.utc).date()

            # Auto-create closure record if one doesn't exist
            closure_result = await db.execute(
                select(ProjectClosureRecord).where(
                    ProjectClosureRecord.project_id == project_id
                )
            )
            if closure_result.scalar_one_or_none() is None:
                closure = ProjectClosureRecord(project_id=project_id)
                db.add(closure)

        await db.flush()
        return ProjectStatus.CLOSED.value

    elif any_started:
        # At least one milestone in progress
        if project.status == ProjectStatus.KICKED_OFF:
            project.status = ProjectStatus.IN_EXECUTION
        await db.flush()
        return project.status.value

    else:
        # No milestones started yet
        return project.status.value
