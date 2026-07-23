from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.modules.pmo_projects.domain.models import (
    Project,
    ProjectStatus,
    ProductLine,
    WeeklyProgressReport,
)
from app.web.deps import get_current_user_from_session
from app.web.utils import render

router = APIRouter(prefix="/pmo", tags=["Web — PMO Projects"])

_PER_PAGE = 20

def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


@router.get("")
async def pmo_root():
    return _redirect("/pmo/projects")


@router.get("/projects")
async def list_projects(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    product_line: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Project)
    count_stmt = select(func.count()).select_from(Project.__table__)

    if search:
        search_filter = or_(
            Project.code.ilike(f"%{search}%"),
            Project.name.ilike(f"%{search}%"),
            Project.project_manager.ilike(f"%{search}%"),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if status:
        stmt = stmt.where(Project.status == status)
        count_stmt = count_stmt.where(Project.status == status)

    if product_line:
        stmt = stmt.where(Project.product_line == product_line)
        count_stmt = count_stmt.where(Project.product_line == product_line)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(Project.created_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/pmo/projects.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "status": status,
        "product_line": product_line,
        "page_title": "PMO Projects",
    })


@router.get("/projects/table")
async def projects_table(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    product_line: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Project)
    count_stmt = select(func.count()).select_from(Project.__table__)

    if search:
        search_filter = or_(
            Project.code.ilike(f"%{search}%"),
            Project.name.ilike(f"%{search}%"),
            Project.project_manager.ilike(f"%{search}%"),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if status:
        stmt = stmt.where(Project.status == status)
        count_stmt = count_stmt.where(Project.status == status)

    if product_line:
        stmt = stmt.where(Project.product_line == product_line)
        count_stmt = count_stmt.where(Project.product_line == product_line)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(Project.created_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/pmo/_projects_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
    })


@router.get("/projects/create")
async def project_create_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/pmo/project_create.html", {
        "page_title": "Create Project",
    })


@router.post("/projects")
async def create_project(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    product_line: str = Form(...),
    project_manager: str = Form(...),
    start_date: date = Form(...),
    budget: Optional[Decimal] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    project = Project(
        code=code,
        name=name,
        product_line=product_line,
        project_manager=project_manager,
        start_date=start_date,
        budget=budget,
        description=description,
        status=ProjectStatus.KICKED_OFF,
    )
    db.add(project)
    await db.commit()
    return _redirect(f"/pmo/projects/{project.id}")


@router.get("/projects/{project_id}")
async def project_detail(
    request: Request,
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Project).options(
        selectinload(Project.weekly_reports),
        selectinload(Project.execution_plans)
    ).where(Project.id == project_id)
    
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        return _redirect("/pmo/projects")

    # Sort reports newest first
    reports = sorted(project.weekly_reports, key=lambda r: (r.year, r.week_number), reverse=True)

    return render(request, "pages/pmo/project_detail.html", {
        "project": project,
        "reports": reports,
        "page_title": f"Project: {project.code}",
    })


@router.post("/projects/{project_id}/reports")
async def create_weekly_report(
    request: Request,
    project_id: int,
    week_number: int = Form(...),
    year: int = Form(...),
    accomplishments: str = Form(...),
    next_week_plan: str = Form(...),
    blockers: Optional[str] = Form(None),
    status_percent: int = Form(0),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    report = WeeklyProgressReport(
        project_id=project_id,
        week_number=week_number,
        year=year,
        accomplishments=accomplishments,
        next_week_plan=next_week_plan,
        blockers=blockers,
        status_percent=status_percent,
    )
    db.add(report)
    await db.commit()
    return _redirect(f"/pmo/projects/{project_id}")
