from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi.responses import RedirectResponse

from app.web.deps import get_current_user_from_session
from app.core.database import get_db
from app.modules.training_services.domain.models import (
    Course,
    CourseModality,
    TrainingSession,
    SessionStatus,
    UserManual,
    VideoTutorial,
)
from app.web.utils import render

router = APIRouter(prefix="/training", tags=["Web — Training Services"])


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


# ─── Courses ─────────────────────────────────────────────────────────────

@router.get("/courses")
async def list_courses(
    request: Request,
    search: Optional[str] = None,
    modality: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Course).where(Course.is_deleted == False)
    
    if search:
        stmt = stmt.where(Course.title.ilike(f"%{search}%") | Course.code.ilike(f"%{search}%"))
    if modality:
        stmt = stmt.where(Course.modality == modality)
        
    stmt = stmt.order_by(Course.created_at.desc())
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/training/courses.html", {
        "items": items,
        "search": search or "",
        "modality": modality or "",
        "page_title": "Training Courses",
    })


@router.get("/courses/create")
async def create_course_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/training/course_create.html", {
        "page_title": "New Training Course",
    })


@router.post("/courses")
async def create_course(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    modality: str = Form(...),
    duration_hours: int = Form(...),
    content: str = Form(""),
    is_sellable: bool = Form(False),
    base_price: float = Form(0.0),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    course = Course(
        code=code,
        title=title,
        modality=modality,
        duration_hours=duration_hours,
        content=content,
        is_sellable=is_sellable,
        base_price=base_price,
        status="draft"
    )
    db.add(course)
    await db.commit()
    return _redirect("/training/courses")


@router.get("/courses/{course_id}")
async def detail_course(
    request: Request,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    # Load course along with its sessions
    stmt = select(Course).options(selectinload(Course.sessions)).where(Course.id == course_id, Course.is_deleted == False)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        return _redirect("/training/courses")

    return render(request, "pages/training/course_detail.html", {
        "item": item,
        "page_title": f"{item.code} — {item.title}",
    })


@router.get("/courses/{course_id}/edit")
async def edit_course_form(
    request: Request,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Course).where(Course.id == course_id, Course.is_deleted == False)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        return _redirect("/training/courses")

    return render(request, "pages/training/course_edit.html", {
        "item": item,
        "page_title": f"Edit Course — {item.code}",
    })


@router.post("/courses/{course_id}/edit")
async def edit_course(
    request: Request,
    course_id: int,
    title: str = Form(...),
    modality: str = Form(...),
    duration_hours: int = Form(...),
    content: str = Form(""),
    status: str = Form("draft"),
    is_sellable: bool = Form(False),
    base_price: float = Form(0.0),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Course).where(Course.id == course_id, Course.is_deleted == False)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    
    if not course:
        return _redirect("/training/courses")

    course.title = title
    course.modality = modality
    course.duration_hours = duration_hours
    course.content = content
    course.status = status
    course.is_sellable = is_sellable
    course.base_price = base_price
    
    await db.commit()
    return _redirect(f"/training/courses/{course_id}")


@router.post("/courses/{course_id}/delete")
async def delete_course(
    request: Request,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(Course).where(Course.id == course_id, Course.is_deleted == False)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    
    if course:
        course.is_deleted = True
        course.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        
    return _redirect("/training/courses")


# ─── Sessions ────────────────────────────────────────────────────────────

@router.post("/courses/{course_id}/sessions")
async def create_session(
    request: Request,
    course_id: int,
    instructor: str = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    session = TrainingSession(
        course_id=course_id,
        instructor=instructor,
        start_date=start_date,
        end_date=end_date,
        status=SessionStatus.SCHEDULED,
    )
    db.add(session)
    await db.commit()
    return _redirect(f"/training/courses/{course_id}")


# ─── Library (Manuals & Videos) ──────────────────────────────────────────

@router.get("/library")
async def list_library(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    manuals_stmt = select(UserManual).where(UserManual.is_deleted == False).order_by(UserManual.code)
    manuals_res = await db.execute(manuals_stmt)
    manuals = list(manuals_res.scalars().all())

    videos_stmt = select(VideoTutorial).where(VideoTutorial.is_deleted == False).order_by(VideoTutorial.code)
    videos_res = await db.execute(videos_stmt)
    videos = list(videos_res.scalars().all())

    return render(request, "pages/training/library.html", {
        "manuals": manuals,
        "videos": videos,
        "page_title": "Training Library",
    })
