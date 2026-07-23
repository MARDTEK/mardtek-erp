from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.core.pagination import PaginationParams
from app.modules.pmo_projects.application.services import pmo_service
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
    page: PaginationParams = Depends(),
    status: str | None = None,
    product_line: str | None = None,
    project_manager: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await pmo_service.list_projects(
        db, page, status=status, product_line=product_line, project_manager=project_manager
    )


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    return await pmo_service.create_project(db, payload.model_dump())


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await pmo_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_project(project_id: int, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    project = await pmo_service.update_project(db, project_id, payload.model_dump(exclude_unset=True))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/progress", response_model=ProgressResponse)
async def get_project_progress(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await pmo_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await pmo_service.calculate_project_progress(project_id, db)


# ─── Execution Plans ─────────────────────────────────────────────────────

@router.get("/projects/{project_id}/execution-plans", response_model=List[ExecutionPlanResponse])
async def list_execution_plans(
    project_id: int,
    page: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await pmo_service.list_execution_plans(db, project_id, page)


@router.post(
    "/projects/{project_id}/execution-plans",
    response_model=ExecutionPlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_execution_plan(project_id: int, payload: ExecutionPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = await pmo_service.create_execution_plan(db, project_id, payload.model_dump())
    if not plan:
        raise HTTPException(status_code=404, detail="Project not found")
    return plan


@router.get("/execution-plans/{plan_id}", response_model=ExecutionPlanResponse)
async def get_execution_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    plan = await pmo_service.get_execution_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Execution plan not found")
    return plan


@router.patch("/execution-plans/{plan_id}", response_model=ExecutionPlanResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_execution_plan(plan_id: int, payload: ExecutionPlanUpdate, db: AsyncSession = Depends(get_db)):
    plan = await pmo_service.update_execution_plan(db, plan_id, payload.model_dump(exclude_unset=True))
    if not plan:
        raise HTTPException(status_code=404, detail="Execution plan not found")
    return plan


# ─── Change Requests ─────────────────────────────────────────────────────

@router.get("/projects/{project_id}/change-requests", response_model=List[ChangeRequestResponse])
async def list_change_requests(
    project_id: int,
    page: PaginationParams = Depends(),
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await pmo_service.list_change_requests(db, project_id, page, status_filter)


@router.post(
    "/projects/{project_id}/change-requests",
    response_model=ChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_change_request(project_id: int, payload: ChangeRequestCreate, db: AsyncSession = Depends(get_db)):
    cr = await pmo_service.create_change_request(db, project_id, payload.model_dump())
    if not cr:
        raise HTTPException(status_code=404, detail="Project not found")
    return cr


@router.get("/change-requests/{cr_id}", response_model=ChangeRequestResponse)
async def get_change_request(cr_id: int, db: AsyncSession = Depends(get_db)):
    cr = await pmo_service.get_change_request(db, cr_id)
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
    return cr


@router.patch("/change-requests/{cr_id}", response_model=ChangeRequestResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_change_request(cr_id: int, payload: ChangeRequestUpdate, db: AsyncSession = Depends(get_db)):
    cr = await pmo_service.update_change_request(db, cr_id, payload.model_dump(exclude_unset=True))
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
    return cr


@router.post("/change-requests/{cr_id}/approve", response_model=ChangeRequestResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def approve_change_request(
    cr_id: int,
    payload: ChangeRequestApprove,
    db: AsyncSession = Depends(get_db),
):
    cr = await pmo_service.get_change_request(db, cr_id)
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
        
    updated_cr = await pmo_service.update_change_request(
        db, cr_id, {"status": "approved", "approved_by": payload.approved_by}
    )

    # Emit event
    await event_bus.emit(Event(
        name="ChangeRequestApproved",
        payload={
            "change_request_id": updated_cr.id,
            "project_id": updated_cr.project_id,
            "code": updated_cr.code,
            "approved_by": payload.approved_by,
        },
        source_module="pmo_projects",
    ))
    return updated_cr


@router.get("/projects/{project_id}/overdue-change-requests", response_model=List[dict])
async def list_overdue_change_requests(project_id: int, db: AsyncSession = Depends(get_db)):
    return await pmo_service.get_overdue_change_requests(db, project_id)


# ─── Weekly Progress Reports ─────────────────────────────────────────────

@router.get("/projects/{project_id}/weekly-reports", response_model=List[WeeklyReportResponse])
async def list_weekly_reports(
    project_id: int,
    page: PaginationParams = Depends(),
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await pmo_service.list_weekly_reports(db, project_id, page, year)


@router.post(
    "/projects/{project_id}/weekly-reports",
    response_model=WeeklyReportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_weekly_report(project_id: int, payload: WeeklyReportCreate, db: AsyncSession = Depends(get_db)):
    report = await pmo_service.create_weekly_report(db, project_id, payload.model_dump())
    if not report:
        raise HTTPException(status_code=404, detail="Project not found")
    return report


@router.get("/weekly-reports/{report_id}", response_model=WeeklyReportResponse)
async def get_weekly_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await pmo_service.get_weekly_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    return report


@router.patch("/weekly-reports/{report_id}", response_model=WeeklyReportResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_weekly_report(report_id: int, payload: WeeklyReportUpdate, db: AsyncSession = Depends(get_db)):
    report = await pmo_service.update_weekly_report(db, report_id, payload.model_dump(exclude_unset=True))
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    return report


# ─── Deliverables Checklist ──────────────────────────────────────────────

@router.get("/projects/{project_id}/deliverables-checklist", response_model=DeliverablesChecklistResponse)
async def get_deliverables_checklist(project_id: int, db: AsyncSession = Depends(get_db)):
    checklist = await pmo_service.get_deliverables_checklist(db, project_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Deliverables checklist not found for this project")
    return checklist


@router.post(
    "/projects/{project_id}/deliverables-checklist",
    response_model=DeliverablesChecklistResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_deliverables_checklist(
    project_id: int,
    payload: DeliverablesChecklistCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await pmo_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    items_data = [item.model_dump() for item in payload.items]
    checklist = await pmo_service.create_deliverables_checklist(db, project_id, items_data)
    if not checklist:
        raise HTTPException(status_code=409, detail="Deliverables checklist already exists for this project")
    return checklist


@router.patch("/projects/{project_id}/deliverables-checklist", response_model=DeliverablesChecklistResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_deliverables_checklist(
    project_id: int,
    payload: DeliverablesChecklistUpdate,
    db: AsyncSession = Depends(get_db),
):
    checklist = await pmo_service.update_deliverables_checklist(db, project_id, payload.model_dump(exclude_unset=True))
    if not checklist:
        raise HTTPException(status_code=404, detail="Deliverables checklist not found")
    return checklist


# ─── Follow-Up Meetings ──────────────────────────────────────────────────

@router.get("/projects/{project_id}/follow-up-meetings", response_model=List[FollowUpMeetingResponse])
async def list_follow_up_meetings(
    project_id: int,
    page: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await pmo_service.list_follow_up_meetings(db, project_id, page)


@router.post(
    "/projects/{project_id}/follow-up-meetings",
    response_model=FollowUpMeetingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_follow_up_meeting(project_id: int, payload: FollowUpMeetingCreate, db: AsyncSession = Depends(get_db)):
    meeting = await pmo_service.create_follow_up_meeting(db, project_id, payload.model_dump())
    if not meeting:
        raise HTTPException(status_code=404, detail="Project not found")
    return meeting


@router.get("/follow-up-meetings/{meeting_id}", response_model=FollowUpMeetingResponse)
async def get_follow_up_meeting(meeting_id: int, db: AsyncSession = Depends(get_db)):
    meeting = await pmo_service.get_follow_up_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Follow-up meeting not found")
    return meeting


@router.patch("/follow-up-meetings/{meeting_id}", response_model=FollowUpMeetingResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_follow_up_meeting(meeting_id: int, payload: FollowUpMeetingUpdate, db: AsyncSession = Depends(get_db)):
    meeting = await pmo_service.update_follow_up_meeting(db, meeting_id, payload.model_dump(exclude_unset=True))
    if not meeting:
        raise HTTPException(status_code=404, detail="Follow-up meeting not found")
    return meeting


# ─── Handover Acceptance ─────────────────────────────────────────────────

@router.get("/projects/{project_id}/handover-acceptance", response_model=HandoverAcceptanceResponse)
async def get_handover_acceptance(project_id: int, db: AsyncSession = Depends(get_db)):
    ha = await pmo_service.get_handover_acceptance(db, project_id)
    if not ha:
        raise HTTPException(status_code=404, detail="Handover acceptance not found for this project")
    return ha


@router.post(
    "/projects/{project_id}/handover-acceptance",
    response_model=HandoverAcceptanceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_handover_acceptance(
    project_id: int,
    payload: HandoverAcceptanceCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await pmo_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ha = await pmo_service.create_handover_acceptance(db, project_id, payload.model_dump())
    if not ha:
        raise HTTPException(status_code=409, detail="Handover acceptance already exists for this project")
    return ha


@router.post("/handover-acceptance/{ha_id}/sign", response_model=HandoverAcceptanceResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def sign_handover_acceptance(ha_id: int, db: AsyncSession = Depends(get_db)):
    ha = await pmo_service.sign_handover_acceptance(db, ha_id)
    if not ha:
        raise HTTPException(status_code=404, detail="Handover acceptance not found")
    return ha


# ─── Project Closure ─────────────────────────────────────────────────────

@router.get("/projects/{project_id}/closure", response_model=ProjectClosureResponse)
async def get_project_closure(project_id: int, db: AsyncSession = Depends(get_db)):
    closure = await pmo_service.get_project_closure(db, project_id)
    if not closure:
        raise HTTPException(status_code=404, detail="Closure record not found for this project")
    return closure


@router.post("/projects/{project_id}/closure", response_model=ProjectClosureResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_project_closure(
    project_id: int,
    payload: ProjectClosureCreate,
    db: AsyncSession = Depends(get_db),
):
    closure = await pmo_service.close_project(
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

@router.post("/projects/{project_id}/sync-milestones", response_model=dict, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def sync_project_milestones(project_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger milestone-based status auto-update for a project."""
    status = await pmo_service.update_project_status_from_milestones(db, project_id)
    return {"project_id": project_id, "status": status}
