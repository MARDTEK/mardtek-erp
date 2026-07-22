from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.modules.pmo_projects.domain.logic import (
    calculate_project_progress,
    close_project,
    get_overdue_change_requests,
    update_project_status_from_milestones,
)
from app.modules.pmo_projects.domain.models import (
    ChangeRequest,
    CRStatus,
    DeliverablesChecklist,
    FollowUpMeeting,
    HandoverAcceptance,
    Project,
    ProjectClosureRecord,
    ProjectExecutionPlan,
    WeeklyProgressReport,
)
from app.modules.pmo_projects.schemas.dto import (
    ChangeRequestApprove,
    ChangeRequestCreate,
    ChangeRequestResponse,
    ChangeRequestUpdate,
    DeliverablesChecklistCreate,
    DeliverablesChecklistResponse,
    DeliverablesChecklistUpdate,
    ExecutionPlanCreate,
    ExecutionPlanResponse,
    ExecutionPlanUpdate,
    FollowUpMeetingCreate,
    FollowUpMeetingResponse,
    FollowUpMeetingUpdate,
    HandoverAcceptanceCreate,
    HandoverAcceptanceResponse,
    ProjectClosureCreate,
    ProjectClosureResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProgressResponse,
    WeeklyReportCreate,
    WeeklyReportResponse,
    WeeklyReportUpdate,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# ─── Projects ────────────────────────────────────────────────────────────

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    status: str | None = None,
    product_line: str | None = None,
    project_manager: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Project)
    if status:
        stmt = stmt.where(Project.status == status)
    if product_line:
        stmt = stmt.where(Project.product_line == product_line)
    if project_manager:
        stmt = stmt.where(Project.project_manager == project_manager)
    result = await db.execute(stmt.order_by(Project.created_at.desc()))
    return list(result.scalars().all())


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(**payload.model_dump())
    db.add(project)
    await db.flush()
    return project


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.flush()
    return project


@router.get("/projects/{project_id}/progress", response_model=ProgressResponse)
async def get_project_progress(project_id: int, db: AsyncSession = Depends(get_db)):
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    return await calculate_project_progress(project_id, db)


# ─── Execution Plans ─────────────────────────────────────────────────────

@router.get("/projects/{project_id}/execution-plans", response_model=List[ExecutionPlanResponse])
async def list_execution_plans(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProjectExecutionPlan)
        .where(ProjectExecutionPlan.project_id == project_id)
        .order_by(ProjectExecutionPlan.created_at.desc())
    )
    return list(result.scalars().all())


@router.post(
    "/projects/{project_id}/execution-plans",
    response_model=ExecutionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_execution_plan(project_id: int, payload: ExecutionPlanCreate, db: AsyncSession = Depends(get_db)):
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    plan = ProjectExecutionPlan(project_id=project_id, **payload.model_dump())
    db.add(plan)
    await db.flush()
    return plan


@router.get("/execution-plans/{plan_id}", response_model=ExecutionPlanResponse)
async def get_execution_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProjectExecutionPlan).where(ProjectExecutionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Execution plan not found")
    return plan


@router.patch("/execution-plans/{plan_id}", response_model=ExecutionPlanResponse)
async def update_execution_plan(plan_id: int, payload: ExecutionPlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProjectExecutionPlan).where(ProjectExecutionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Execution plan not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.flush()
    return plan


# ─── Change Requests ─────────────────────────────────────────────────────

@router.get("/projects/{project_id}/change-requests", response_model=List[ChangeRequestResponse])
async def list_change_requests(
    project_id: int,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChangeRequest).where(ChangeRequest.project_id == project_id)
    if status_filter:
        stmt = stmt.where(ChangeRequest.status == status_filter)
    result = await db.execute(stmt.order_by(ChangeRequest.created_at.desc()))
    return list(result.scalars().all())


@router.post(
    "/projects/{project_id}/change-requests",
    response_model=ChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_change_request(project_id: int, payload: ChangeRequestCreate, db: AsyncSession = Depends(get_db)):
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    cr = ChangeRequest(project_id=project_id, **payload.model_dump())
    db.add(cr)
    await db.flush()
    return cr


@router.get("/change-requests/{cr_id}", response_model=ChangeRequestResponse)
async def get_change_request(cr_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChangeRequest).where(ChangeRequest.id == cr_id))
    cr = result.scalar_one_or_none()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
    return cr


@router.patch("/change-requests/{cr_id}", response_model=ChangeRequestResponse)
async def update_change_request(cr_id: int, payload: ChangeRequestUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChangeRequest).where(ChangeRequest.id == cr_id))
    cr = result.scalar_one_or_none()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cr, field, value)
    await db.flush()
    return cr


@router.post("/change-requests/{cr_id}/approve", response_model=ChangeRequestResponse)
async def approve_change_request(
    cr_id: int,
    payload: ChangeRequestApprove,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ChangeRequest).where(ChangeRequest.id == cr_id))
    cr = result.scalar_one_or_none()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
    cr.status = CRStatus.APPROVED
    cr.approved_by = payload.approved_by
    await db.flush()

    # Emit event
    await event_bus.emit(Event(
        name="ChangeRequestApproved",
        payload={
            "change_request_id": cr.id,
            "project_id": cr.project_id,
            "code": cr.code,
            "approved_by": payload.approved_by,
        },
        source_module="pmo_projects",
    ))
    return cr


@router.get("/projects/{project_id}/overdue-change-requests", response_model=List[dict])
async def list_overdue_change_requests(project_id: int, db: AsyncSession = Depends(get_db)):
    return await get_overdue_change_requests(db, project_id)


# ─── Weekly Progress Reports ─────────────────────────────────────────────

@router.get("/projects/{project_id}/weekly-reports", response_model=List[WeeklyReportResponse])
async def list_weekly_reports(
    project_id: int,
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(WeeklyProgressReport)
        .where(WeeklyProgressReport.project_id == project_id)
    )
    if year:
        stmt = stmt.where(WeeklyProgressReport.year == year)
    result = await db.execute(stmt.order_by(WeeklyProgressReport.year.desc(), WeeklyProgressReport.week_number.desc()))
    return list(result.scalars().all())


@router.post(
    "/projects/{project_id}/weekly-reports",
    response_model=WeeklyReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_weekly_report(project_id: int, payload: WeeklyReportCreate, db: AsyncSession = Depends(get_db)):
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    report = WeeklyProgressReport(project_id=project_id, **payload.model_dump())
    db.add(report)
    await db.flush()
    return report


@router.get("/weekly-reports/{report_id}", response_model=WeeklyReportResponse)
async def get_weekly_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeeklyProgressReport).where(WeeklyProgressReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    return report


@router.patch("/weekly-reports/{report_id}", response_model=WeeklyReportResponse)
async def update_weekly_report(report_id: int, payload: WeeklyReportUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeeklyProgressReport).where(WeeklyProgressReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    await db.flush()
    return report


# ─── Deliverables Checklist ──────────────────────────────────────────────

@router.get("/projects/{project_id}/deliverables-checklist", response_model=DeliverablesChecklistResponse)
async def get_deliverables_checklist(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DeliverablesChecklist).where(DeliverablesChecklist.project_id == project_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="Deliverables checklist not found for this project")
    return checklist


@router.post(
    "/projects/{project_id}/deliverables-checklist",
    response_model=DeliverablesChecklistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_deliverables_checklist(
    project_id: int,
    payload: DeliverablesChecklistCreate,
    db: AsyncSession = Depends(get_db),
):
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    # Check existing
    existing = await db.execute(
        select(DeliverablesChecklist).where(DeliverablesChecklist.project_id == project_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Deliverables checklist already exists for this project")

    items_data = [item.model_dump() for item in payload.items]
    checklist = DeliverablesChecklist(project_id=project_id, items=items_data)
    db.add(checklist)
    await db.flush()
    return checklist


@router.patch("/projects/{project_id}/deliverables-checklist", response_model=DeliverablesChecklistResponse)
async def update_deliverables_checklist(
    project_id: int,
    payload: DeliverablesChecklistUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeliverablesChecklist).where(DeliverablesChecklist.project_id == project_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="Deliverables checklist not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "items" and value is not None:
            checklist.items = [item.model_dump() if hasattr(item, "model_dump") else item for item in value]
        else:
            setattr(checklist, field, value)
    await db.flush()
    return checklist


# ─── Follow-Up Meetings ──────────────────────────────────────────────────

@router.get("/projects/{project_id}/follow-up-meetings", response_model=List[FollowUpMeetingResponse])
async def list_follow_up_meetings(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FollowUpMeeting)
        .where(FollowUpMeeting.project_id == project_id)
        .order_by(FollowUpMeeting.date.desc())
    )
    return list(result.scalars().all())


@router.post(
    "/projects/{project_id}/follow-up-meetings",
    response_model=FollowUpMeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_follow_up_meeting(project_id: int, payload: FollowUpMeetingCreate, db: AsyncSession = Depends(get_db)):
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    meeting = FollowUpMeeting(project_id=project_id, **payload.model_dump())
    db.add(meeting)
    await db.flush()
    return meeting


@router.get("/follow-up-meetings/{meeting_id}", response_model=FollowUpMeetingResponse)
async def get_follow_up_meeting(meeting_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FollowUpMeeting).where(FollowUpMeeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Follow-up meeting not found")
    return meeting


@router.patch("/follow-up-meetings/{meeting_id}", response_model=FollowUpMeetingResponse)
async def update_follow_up_meeting(meeting_id: int, payload: FollowUpMeetingUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FollowUpMeeting).where(FollowUpMeeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Follow-up meeting not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(meeting, field, value)
    await db.flush()
    return meeting


# ─── Handover Acceptance ─────────────────────────────────────────────────

@router.get("/projects/{project_id}/handover-acceptance", response_model=HandoverAcceptanceResponse)
async def get_handover_acceptance(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HandoverAcceptance).where(HandoverAcceptance.project_id == project_id)
    )
    ha = result.scalar_one_or_none()
    if not ha:
        raise HTTPException(status_code=404, detail="Handover acceptance not found for this project")
    return ha


@router.post(
    "/projects/{project_id}/handover-acceptance",
    response_model=HandoverAcceptanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_handover_acceptance(
    project_id: int,
    payload: HandoverAcceptanceCreate,
    db: AsyncSession = Depends(get_db),
):
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    existing = await db.execute(
        select(HandoverAcceptance).where(HandoverAcceptance.project_id == project_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Handover acceptance already exists for this project")

    ha = HandoverAcceptance(project_id=project_id, **payload.model_dump())
    db.add(ha)
    await db.flush()
    return ha


@router.post("/handover-acceptance/{ha_id}/sign", response_model=HandoverAcceptanceResponse)
async def sign_handover_acceptance(ha_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HandoverAcceptance).where(HandoverAcceptance.id == ha_id))
    ha = result.scalar_one_or_none()
    if not ha:
        raise HTTPException(status_code=404, detail="Handover acceptance not found")
    ha.status = "signed"
    await db.flush()
    return ha


# ─── Project Closure ─────────────────────────────────────────────────────

@router.get("/projects/{project_id}/closure", response_model=ProjectClosureResponse)
async def get_project_closure(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProjectClosureRecord).where(ProjectClosureRecord.project_id == project_id)
    )
    closure = result.scalar_one_or_none()
    if not closure:
        raise HTTPException(status_code=404, detail="Closure record not found for this project")
    return closure


@router.post("/projects/{project_id}/closure", response_model=ProjectClosureResponse, status_code=status.HTTP_201_CREATED)
async def create_project_closure(
    project_id: int,
    payload: ProjectClosureCreate,
    db: AsyncSession = Depends(get_db),
):
    closure = await close_project(
        db,
        project_id,
        lessons_learned=payload.lessons_learned,
        final_budget=payload.final_budget,
        customer_feedback=payload.customer_feedback,
    )
    if not closure:
        raise HTTPException(
            status_code=409,
            detail="Cannot close project. Verify all deliverables are completed and no open change requests remain.",
        )

    # Emit event
    await event_bus.emit(Event(
        name="ProjectClosed",
        payload={
            "project_id": project_id,
            "closure_id": closure.id,
            "final_budget": str(payload.final_budget) if payload.final_budget else None,
        },
        source_module="pmo_projects",
    ))
    return closure


# ─── Milestone Auto-Update ───────────────────────────────────────────────

@router.post("/projects/{project_id}/sync-milestones", response_model=dict)
async def sync_project_milestones(project_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger milestone-based status auto-update for a project."""
    status = await update_project_status_from_milestones(db, project_id)
    return {"project_id": project_id, "status": status}
