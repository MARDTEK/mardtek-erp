"""Application services for P5 — Project Implementation & Execution."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.pagination import PaginationParams, paginate

from app.modules.pmo_projects.domain.models import (
    ChangeRequest,
    CRStatus,
    ChecklistStatus,
    ClosureStatus,
    DeliverablesChecklist,
    HandoverStatus,
    Project,
    ProjectClosureRecord,
    ProjectExecutionPlan,
    ProjectStatus,
    WeeklyProgressReport,
    FollowUpMeeting,
    HandoverAcceptance
)
from app.modules.pmo_projects.infrastructure.repositories import (
    change_request_repo,
    closure_record_repo,
    deliverables_checklist_repo,
    execution_plan_repo,
    project_repo,
    weekly_report_repo,
    follow_up_meeting_repo,
    handover_acceptance_repo
)


class PMOProjectService:
    # ─── Projects ────────────────────────────────────────────────────────────

    @staticmethod
    async def list_projects(
        db: AsyncSession,
        page: PaginationParams,
        status: str | None = None,
        product_line: str | None = None,
        project_manager: str | None = None,
    ) -> List[Project]:
        stmt = select(Project)
        if status:
            stmt = stmt.where(Project.status == status)
        if product_line:
            stmt = stmt.where(Project.product_line == product_line)
        if project_manager:
            stmt = stmt.where(Project.project_manager == project_manager)
        
        result = await db.execute(paginate(stmt.order_by(Project.created_at.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_project(db: AsyncSession, data: dict) -> Project:
        project = Project(**data)
        project_repo.add(db, project)
        await db.flush()
        return project

    @staticmethod
    async def get_project(db: AsyncSession, project_id: int) -> Optional[Project]:
        return await project_repo.get_by_id(db, project_id)

    @staticmethod
    async def update_project(db: AsyncSession, project_id: int, data: dict) -> Optional[Project]:
        project = await project_repo.get_by_id(db, project_id)
        if not project:
            return None
        for field, value in data.items():
            setattr(project, field, value)
        await db.flush()
        return project

    @staticmethod
    async def calculate_project_progress(project_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Calculate project completion percentage based on deliverables checklist."""
        checklist = await deliverables_checklist_repo.get_by_project(db, project_id)

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

    # ─── Execution Plans ─────────────────────────────────────────────────────

    @staticmethod
    async def list_execution_plans(db: AsyncSession, project_id: int, page: PaginationParams) -> List[ProjectExecutionPlan]:
        stmt = select(ProjectExecutionPlan).where(ProjectExecutionPlan.project_id == project_id).order_by(ProjectExecutionPlan.created_at.desc())
        result = await db.execute(paginate(stmt, page))
        return list(result.scalars().all())

    @staticmethod
    async def create_execution_plan(db: AsyncSession, project_id: int, data: dict) -> Optional[ProjectExecutionPlan]:
        project = await project_repo.get_by_id(db, project_id)
        if not project:
            return None
        plan = ProjectExecutionPlan(project_id=project_id, **data)
        execution_plan_repo.add(db, plan)
        await db.flush()
        return plan

    @staticmethod
    async def get_execution_plan(db: AsyncSession, plan_id: int) -> Optional[ProjectExecutionPlan]:
        return await execution_plan_repo.get_by_id(db, plan_id)

    @staticmethod
    async def update_execution_plan(db: AsyncSession, plan_id: int, data: dict) -> Optional[ProjectExecutionPlan]:
        plan = await execution_plan_repo.get_by_id(db, plan_id)
        if not plan:
            return None
        for field, value in data.items():
            setattr(plan, field, value)
        await db.flush()
        return plan

    # ─── Change Requests ─────────────────────────────────────────────────────

    @staticmethod
    async def list_change_requests(db: AsyncSession, project_id: int, page: PaginationParams, status_filter: str | None = None) -> List[ChangeRequest]:
        stmt = select(ChangeRequest).where(ChangeRequest.project_id == project_id)
        if status_filter:
            stmt = stmt.where(ChangeRequest.status == status_filter)
        result = await db.execute(paginate(stmt.order_by(ChangeRequest.created_at.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_change_request(db: AsyncSession, project_id: int, data: dict) -> Optional[ChangeRequest]:
        project = await project_repo.get_by_id(db, project_id)
        if not project:
            return None
        cr = ChangeRequest(project_id=project_id, **data)
        change_request_repo.add(db, cr)
        await db.flush()
        return cr

    @staticmethod
    async def get_change_request(db: AsyncSession, cr_id: int) -> Optional[ChangeRequest]:
        return await change_request_repo.get_by_id(db, cr_id)

    @staticmethod
    async def update_change_request(db: AsyncSession, cr_id: int, data: dict) -> Optional[ChangeRequest]:
        cr = await change_request_repo.get_by_id(db, cr_id)
        if not cr:
            return None
        for field, value in data.items():
            setattr(cr, field, value)
        await db.flush()
        return cr
    
    @staticmethod
    async def get_overdue_change_requests(
        db: AsyncSession, project_id: int
    ) -> List[dict]:
        """Return change requests that are still submitted (pending approval/rejection)."""
        crs = await change_request_repo.get_open_by_project(db, project_id)
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

    # ─── Weekly Progress Reports ─────────────────────────────────────────────

    @staticmethod
    async def list_weekly_reports(db: AsyncSession, project_id: int, page: PaginationParams, year: int | None = None) -> List[WeeklyProgressReport]:
        stmt = select(WeeklyProgressReport).where(WeeklyProgressReport.project_id == project_id)
        if year:
            stmt = stmt.where(WeeklyProgressReport.year == year)
        result = await db.execute(paginate(stmt.order_by(WeeklyProgressReport.year.desc(), WeeklyProgressReport.week_number.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_weekly_report(db: AsyncSession, project_id: int, data: dict) -> Optional[WeeklyProgressReport]:
        project = await project_repo.get_by_id(db, project_id)
        if not project:
            return None
        report = WeeklyProgressReport(project_id=project_id, **data)
        weekly_report_repo.add(db, report)
        await db.flush()
        return report

    @staticmethod
    async def get_weekly_report(db: AsyncSession, report_id: int) -> Optional[WeeklyProgressReport]:
        return await weekly_report_repo.get_by_id(db, report_id)

    @staticmethod
    async def update_weekly_report(db: AsyncSession, report_id: int, data: dict) -> Optional[WeeklyProgressReport]:
        report = await weekly_report_repo.get_by_id(db, report_id)
        if not report:
            return None
        for field, value in data.items():
            setattr(report, field, value)
        await db.flush()
        return report

    # ─── Deliverables Checklist ──────────────────────────────────────────────

    @staticmethod
    async def get_deliverables_checklist(db: AsyncSession, project_id: int) -> Optional[DeliverablesChecklist]:
        return await deliverables_checklist_repo.get_by_project(db, project_id)

    @staticmethod
    async def create_deliverables_checklist(db: AsyncSession, project_id: int, items_data: list) -> Optional[DeliverablesChecklist]:
        project = await project_repo.get_by_id(db, project_id)
        if not project:
            return None
        existing = await deliverables_checklist_repo.get_by_project(db, project_id)
        if existing:
            return None # Conflict
        
        checklist = DeliverablesChecklist(project_id=project_id, items=items_data)
        deliverables_checklist_repo.add(db, checklist)
        await db.flush()
        return checklist

    @staticmethod
    async def update_deliverables_checklist(db: AsyncSession, project_id: int, data: dict) -> Optional[DeliverablesChecklist]:
        checklist = await deliverables_checklist_repo.get_by_project(db, project_id)
        if not checklist:
            return None
        for field, value in data.items():
            if field == "items" and value is not None:
                checklist.items = [item.model_dump() if hasattr(item, "model_dump") else item for item in value]
            else:
                setattr(checklist, field, value)
        await db.flush()
        return checklist

    # ─── Follow-Up Meetings ──────────────────────────────────────────────────

    @staticmethod
    async def list_follow_up_meetings(db: AsyncSession, project_id: int, page: PaginationParams) -> List[FollowUpMeeting]:
        stmt = select(FollowUpMeeting).where(FollowUpMeeting.project_id == project_id).order_by(FollowUpMeeting.date.desc())
        result = await db.execute(paginate(stmt, page))
        return list(result.scalars().all())

    @staticmethod
    async def create_follow_up_meeting(db: AsyncSession, project_id: int, data: dict) -> Optional[FollowUpMeeting]:
        project = await project_repo.get_by_id(db, project_id)
        if not project:
            return None
        meeting = FollowUpMeeting(project_id=project_id, **data)
        follow_up_meeting_repo.add(db, meeting)
        await db.flush()
        return meeting

    @staticmethod
    async def get_follow_up_meeting(db: AsyncSession, meeting_id: int) -> Optional[FollowUpMeeting]:
        return await follow_up_meeting_repo.get_by_id(db, meeting_id)

    @staticmethod
    async def update_follow_up_meeting(db: AsyncSession, meeting_id: int, data: dict) -> Optional[FollowUpMeeting]:
        meeting = await follow_up_meeting_repo.get_by_id(db, meeting_id)
        if not meeting:
            return None
        for field, value in data.items():
            setattr(meeting, field, value)
        await db.flush()
        return meeting

    # ─── Handover Acceptance ─────────────────────────────────────────────────

    @staticmethod
    async def get_handover_acceptance(db: AsyncSession, project_id: int) -> Optional[HandoverAcceptance]:
        return await handover_acceptance_repo.get_by_project(db, project_id)

    @staticmethod
    async def create_handover_acceptance(db: AsyncSession, project_id: int, data: dict) -> Optional[HandoverAcceptance]:
        project = await project_repo.get_by_id(db, project_id)
        if not project:
            return None
        existing = await handover_acceptance_repo.get_by_project(db, project_id)
        if existing:
            return None # Conflict
        
        ha = HandoverAcceptance(project_id=project_id, **data)
        handover_acceptance_repo.add(db, ha)
        await db.flush()
        return ha
    
    @staticmethod
    async def sign_handover_acceptance(db: AsyncSession, ha_id: int) -> Optional[HandoverAcceptance]:
        ha = await handover_acceptance_repo.get_by_id(db, ha_id)
        if not ha:
            return None
        ha.status = "signed"
        await db.flush()
        return ha

    # ─── Project Closure ─────────────────────────────────────────────────────

    @staticmethod
    async def get_project_closure(db: AsyncSession, project_id: int) -> Optional[ProjectClosureRecord]:
        return await closure_record_repo.get_by_project(db, project_id)

    @staticmethod
    async def close_project(
        db: AsyncSession,
        project_id: int,
        lessons_learned: Optional[str] = None,
        final_budget: Optional[Decimal] = None,
        customer_feedback: Optional[str] = None,
    ) -> Optional[ProjectClosureRecord]:
        """Close a project after verifying all deliverables are done."""
        project = await project_repo.get_by_id(db, project_id)
        if project is None:
            return None

        # Verify deliverables are all complete
        checklist = await deliverables_checklist_repo.get_by_project(db, project_id)
        if checklist is not None:
            items = list(checklist.items) if checklist.items else []
            incomplete = [item for item in items if not item.get("completed_at")]
            if incomplete:
                return None

        # Verify no open change requests
        open_crs = await change_request_repo.get_open_by_project(db, project_id)
        if open_crs:
            return None

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
        closure_record_repo.add(db, closure)
        await db.flush()
        return closure

    @staticmethod
    async def update_project_status_from_milestones(
        db: AsyncSession, project_id: int
    ) -> str:
        """Auto-update project status based on execution plan milestones."""
        project = await project_repo.get_by_id(db, project_id)
        if project is None:
            return "not_found"

        plan = await execution_plan_repo.get_by_project(db, project_id)
        if plan is None or not plan.milestones:
            return project.status.value

        milestones = list(plan.milestones)
        total = len(milestones)
        completed = sum(1 for m in milestones if m.get("completed_at"))
        any_started = any(m.get("completed_at") for m in milestones)

        if completed == total and total > 0:
            if project.status != ProjectStatus.CLOSED:
                project.status = ProjectStatus.CLOSED
                project.end_date = datetime.now(timezone.utc).date()

                existing_closure = await closure_record_repo.get_by_project(db, project_id)
                if existing_closure is None:
                    closure = ProjectClosureRecord(project_id=project_id)
                    closure_record_repo.add(db, closure)

            await db.flush()
            return ProjectStatus.CLOSED.value

        elif any_started:
            if project.status == ProjectStatus.KICKED_OFF:
                project.status = ProjectStatus.IN_EXECUTION
            await db.flush()
            return project.status.value

        else:
            return project.status.value


pmo_service = PMOProjectService()
