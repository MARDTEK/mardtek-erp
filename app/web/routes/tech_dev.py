"""Web routes for Tech Development — Roadmaps, Releases, Specs, Risks, QA, Deploys, UAT, Sunsets."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.tech_development.domain.models import (
    DeploymentRecord,
    ProductRoadmap,
    QATestReport,
    ReleasePlan,
    RiskMatrix,
    SolutionSunset,
    TechnicalSpecification,
    UATSignOff,
)
from app.web.deps import get_current_user_from_session
from app.web.utils import render

router = APIRouter(prefix="/development", tags=["Web — Tech Development"])

_PER_PAGE = 20


# ─── Helpers ──────────────────────────────────────────────────────────────


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


# ─── Root ────────────────────────────────────────────────────────────────


@router.get("")
async def development_root():
    return _redirect("/development/roadmaps")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Product Roadmaps
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/roadmaps")
async def list_roadmaps(
    request: Request,
    page: int = 1,
    search: str = "",
    product_line: str = "",
    year: Optional[int] = None,
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(ProductRoadmap).where(ProductRoadmap.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(ProductRoadmap.__table__).where(ProductRoadmap.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            ProductRoadmap.code.ilike(f"%{search}%"),
            ProductRoadmap.title.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if product_line:
        stmt = stmt.where(ProductRoadmap.product_line == product_line)
        count_stmt = count_stmt.where(ProductRoadmap.product_line == product_line)
    if year:
        stmt = stmt.where(ProductRoadmap.year == year)
        count_stmt = count_stmt.where(ProductRoadmap.year == year)
    if status:
        stmt = stmt.where(ProductRoadmap.status == status)
        count_stmt = count_stmt.where(ProductRoadmap.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(ProductRoadmap.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/tech_dev/roadmaps.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "product_line": product_line,
        "year": year,
        "status": status,
        "page_title": "Product Roadmaps",
    })


@router.get("/roadmaps/table")
async def roadmaps_table(
    request: Request,
    page: int = 1,
    search: str = "",
    product_line: str = "",
    year: Optional[int] = None,
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(ProductRoadmap).where(ProductRoadmap.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(ProductRoadmap.__table__).where(ProductRoadmap.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            ProductRoadmap.code.ilike(f"%{search}%"),
            ProductRoadmap.title.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if product_line:
        stmt = stmt.where(ProductRoadmap.product_line == product_line)
        count_stmt = count_stmt.where(ProductRoadmap.product_line == product_line)
    if year:
        stmt = stmt.where(ProductRoadmap.year == year)
        count_stmt = count_stmt.where(ProductRoadmap.year == year)
    if status:
        stmt = stmt.where(ProductRoadmap.status == status)
        count_stmt = count_stmt.where(ProductRoadmap.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(ProductRoadmap.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/tech_dev/_roadmaps_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "product_line": product_line,
        "year": year,
        "status": status,
    })


@router.get("/roadmaps/create")
async def create_roadmap_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/tech_dev/roadmap_create.html", {
        "page_title": "Create Product Roadmap",
    })


@router.get("/roadmaps/{roadmap_id}")
async def detail_roadmap(
    request: Request,
    roadmap_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ProductRoadmap).where(ProductRoadmap.id == roadmap_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/roadmaps")
    return render(request, "pages/tech_dev/roadmap_detail.html", {
        "item": item,
        "page_title": f"Roadmap {item.code}",
    })


@router.get("/roadmaps/{roadmap_id}/edit")
async def edit_roadmap_form(
    request: Request,
    roadmap_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ProductRoadmap).where(ProductRoadmap.id == roadmap_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/roadmaps")
    return render(request, "pages/tech_dev/roadmap_edit.html", {
        "item": item,
        "page_title": f"Edit Roadmap {item.code}",
    })


@router.post("/roadmaps")
async def create_roadmap(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    product_line: str = Form(...),
    year: int = Form(...),
    vision: str = Form(...),
    strategic_goals: str = Form(...),
    items_json: str = Form("[]"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    items_data = []
    if items_json:
        try:
            items_data = json.loads(items_json)
        except json.JSONDecodeError:
            items_data = []

    item = ProductRoadmap(
        code=code,
        title=title,
        product_line=product_line,
        year=year,
        vision=vision,
        strategic_goals=strategic_goals,
        items=items_data,
        status="draft",
    )
    db.add(item)
    await db.commit()
    return _redirect("/development/roadmaps")


@router.post("/roadmaps/{roadmap_id}/edit")
async def edit_roadmap(
    request: Request,
    roadmap_id: int,
    title: str = Form(...),
    vision: str = Form(...),
    strategic_goals: str = Form(...),
    items_json: str = Form("[]"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ProductRoadmap).where(ProductRoadmap.id == roadmap_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/roadmaps")

    items_data = []
    if items_json:
        try:
            items_data = json.loads(items_json)
        except json.JSONDecodeError:
            items_data = []

    item.title = title
    item.vision = vision
    item.strategic_goals = strategic_goals
    item.items = items_data
    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return _redirect(f"/development/roadmaps/{roadmap_id}")


@router.post("/roadmaps/{roadmap_id}/publish")
async def publish_roadmap(
    request: Request,
    roadmap_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ProductRoadmap).where(ProductRoadmap.id == roadmap_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "published"
        item.updated_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/development/roadmaps/{roadmap_id}")


@router.post("/roadmaps/{roadmap_id}/delete")
async def delete_roadmap(
    request: Request,
    roadmap_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ProductRoadmap).where(ProductRoadmap.id == roadmap_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/development/roadmaps")


@router.post("/roadmaps/{roadmap_id}/restore")
async def restore_roadmap(
    request: Request,
    roadmap_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ProductRoadmap).where(ProductRoadmap.id == roadmap_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = False
        item.deleted_at = None
        await db.commit()
    return _redirect(f"/development/roadmaps/{roadmap_id}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Release Plans
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/releases")
async def list_releases(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    product: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(ReleasePlan).where(ReleasePlan.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(ReleasePlan.__table__).where(ReleasePlan.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            ReleasePlan.code.ilike(f"%{search}%"),
            ReleasePlan.title.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if status:
        stmt = stmt.where(ReleasePlan.status == status)
        count_stmt = count_stmt.where(ReleasePlan.status == status)
    if product:
        stmt = stmt.where(ReleasePlan.product.ilike(f"%{product}%"))
        count_stmt = count_stmt.where(ReleasePlan.product.ilike(f"%{product}%"))

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(ReleasePlan.planned_date.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/tech_dev/releases.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "status": status,
        "product": product,
        "page_title": "Release Plans",
    })


@router.get("/releases/table")
async def releases_table(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    product: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(ReleasePlan).where(ReleasePlan.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(ReleasePlan.__table__).where(ReleasePlan.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            ReleasePlan.code.ilike(f"%{search}%"),
            ReleasePlan.title.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if status:
        stmt = stmt.where(ReleasePlan.status == status)
        count_stmt = count_stmt.where(ReleasePlan.status == status)
    if product:
        stmt = stmt.where(ReleasePlan.product.ilike(f"%{product}%"))
        count_stmt = count_stmt.where(ReleasePlan.product.ilike(f"%{product}%"))

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(ReleasePlan.planned_date.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/tech_dev/_releases_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "status": status,
        "product": product,
    })


@router.get("/releases/create")
async def create_release_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/tech_dev/release_create.html", {
        "page_title": "Create Release Plan",
    })


@router.get("/releases/{release_id}")
async def detail_release(
    request: Request,
    release_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/releases")
    return render(request, "pages/tech_dev/release_detail.html", {
        "item": item,
        "page_title": f"Release {item.code}",
    })


@router.get("/releases/{release_id}/edit")
async def edit_release_form(
    request: Request,
    release_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/releases")
    return render(request, "pages/tech_dev/release_edit.html", {
        "item": item,
        "page_title": f"Edit Release {item.code}",
    })


@router.post("/releases")
async def create_release(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    version: str = Form(...),
    product: str = Form(...),
    planned_date: date = Form(...),
    features_json: str = Form("[]"),
    release_notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    features_data = []
    if features_json:
        try:
            features_data = json.loads(features_json)
        except json.JSONDecodeError:
            features_data = []

    item = ReleasePlan(
        code=code,
        title=title,
        version=version,
        product=product,
        planned_date=planned_date,
        features=features_data,
        release_notes=release_notes or None,
        status="planned",
    )
    db.add(item)
    await db.commit()
    return _redirect("/development/releases")


@router.post("/releases/{release_id}/edit")
async def edit_release(
    request: Request,
    release_id: int,
    title: str = Form(...),
    version: str = Form(...),
    planned_date: date = Form(...),
    actual_date: Optional[date] = Form(None),
    features_json: str = Form("[]"),
    release_notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/releases")

    features_data = []
    if features_json:
        try:
            features_data = json.loads(features_json)
        except json.JSONDecodeError:
            features_data = []

    item.title = title
    item.version = version
    item.planned_date = planned_date
    item.actual_date = actual_date
    item.features = features_data
    item.release_notes = release_notes or None
    await db.commit()
    return _redirect(f"/development/releases/{release_id}")


@router.post("/releases/{release_id}/deploy")
async def deploy_release(
    request: Request,
    release_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "in_progress"
        await db.commit()
    return _redirect(f"/development/releases/{release_id}")


@router.post("/releases/{release_id}/complete")
async def complete_release(
    request: Request,
    release_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "deployed"
        item.actual_date = date.today()
        await db.commit()
    return _redirect(f"/development/releases/{release_id}")


@router.post("/releases/{release_id}/rollback")
async def rollback_release(
    request: Request,
    release_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "rolled_back"
        await db.commit()
    return _redirect(f"/development/releases/{release_id}")


@router.post("/releases/{release_id}/delete")
async def delete_release(
    request: Request,
    release_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/development/releases")


@router.post("/releases/{release_id}/restore")
async def restore_release(
    request: Request,
    release_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = False
        item.deleted_at = None
        await db.commit()
    return _redirect(f"/development/releases/{release_id}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Technical Specifications
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/specifications")
async def list_specifications(
    request: Request,
    page: int = 1,
    search: str = "",
    project_id: Optional[int] = None,
    product: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(TechnicalSpecification).where(TechnicalSpecification.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(TechnicalSpecification.__table__).where(TechnicalSpecification.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            TechnicalSpecification.code.ilike(f"%{search}%"),
            TechnicalSpecification.title.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if project_id is not None:
        stmt = stmt.where(TechnicalSpecification.project_id == project_id)
        count_stmt = count_stmt.where(TechnicalSpecification.project_id == project_id)
    if product:
        stmt = stmt.where(TechnicalSpecification.product.ilike(f"%{product}%"))
        count_stmt = count_stmt.where(TechnicalSpecification.product.ilike(f"%{product}%"))
    if status:
        stmt = stmt.where(TechnicalSpecification.status == status)
        count_stmt = count_stmt.where(TechnicalSpecification.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(TechnicalSpecification.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/tech_dev/specifications.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "project_id": project_id,
        "product": product,
        "status": status,
        "page_title": "Technical Specifications",
    })


@router.get("/specifications/table")
async def specifications_table(
    request: Request,
    page: int = 1,
    search: str = "",
    project_id: Optional[int] = None,
    product: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(TechnicalSpecification).where(TechnicalSpecification.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(TechnicalSpecification.__table__).where(TechnicalSpecification.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            TechnicalSpecification.code.ilike(f"%{search}%"),
            TechnicalSpecification.title.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if project_id is not None:
        stmt = stmt.where(TechnicalSpecification.project_id == project_id)
        count_stmt = count_stmt.where(TechnicalSpecification.project_id == project_id)
    if product:
        stmt = stmt.where(TechnicalSpecification.product.ilike(f"%{product}%"))
        count_stmt = count_stmt.where(TechnicalSpecification.product.ilike(f"%{product}%"))
    if status:
        stmt = stmt.where(TechnicalSpecification.status == status)
        count_stmt = count_stmt.where(TechnicalSpecification.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(TechnicalSpecification.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/tech_dev/_specifications_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "project_id": project_id,
        "product": product,
        "status": status,
    })


@router.get("/specifications/create")
async def create_specification_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/tech_dev/specification_create.html", {
        "page_title": "Create Technical Specification",
    })


@router.get("/specifications/{spec_id}")
async def detail_specification(
    request: Request,
    spec_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/specifications")
    return render(request, "pages/tech_dev/specification_detail.html", {
        "item": item,
        "page_title": f"Spec {item.code}",
    })


@router.get("/specifications/{spec_id}/edit")
async def edit_specification_form(
    request: Request,
    spec_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/specifications")
    return render(request, "pages/tech_dev/specification_edit.html", {
        "item": item,
        "page_title": f"Edit Spec {item.code}",
    })


@router.post("/specifications")
async def create_specification(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    project_id: Optional[int] = Form(None),
    product: Optional[str] = Form(None),
    version: str = Form("1.0"),
    content: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = TechnicalSpecification(
        code=code,
        title=title,
        project_id=project_id,
        product=product,
        version=version,
        content=content,
        status="draft",
    )
    db.add(item)
    await db.commit()
    return _redirect("/development/specifications")


@router.post("/specifications/{spec_id}/edit")
async def edit_specification(
    request: Request,
    spec_id: int,
    title: str = Form(...),
    content: str = Form(...),
    version: str = Form("1.0"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/specifications")
    item.title = title
    item.content = content
    item.version = version
    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return _redirect(f"/development/specifications/{spec_id}")


@router.post("/specifications/{spec_id}/review")
async def review_specification(
    request: Request,
    spec_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "reviewed"
        item.updated_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/development/specifications/{spec_id}")


@router.post("/specifications/{spec_id}/approve")
async def approve_specification(
    request: Request,
    spec_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "approved"
        item.approved_by = user.username
        item.updated_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect(f"/development/specifications/{spec_id}")


@router.post("/specifications/{spec_id}/delete")
async def delete_specification(
    request: Request,
    spec_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/development/specifications")


@router.post("/specifications/{spec_id}/restore")
async def restore_specification(
    request: Request,
    spec_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = False
        item.deleted_at = None
        await db.commit()
    return _redirect(f"/development/specifications/{spec_id}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Risk Matrices
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/risk-matrices")
async def list_risk_matrices(
    request: Request,
    page: int = 1,
    search: str = "",
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(RiskMatrix).where(RiskMatrix.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(RiskMatrix.__table__).where(RiskMatrix.is_deleted == False)  # noqa: E712

    if search:
        flt = RiskMatrix.code.ilike(f"%{search}%")
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if project_id is not None:
        stmt = stmt.where(RiskMatrix.project_id == project_id)
        count_stmt = count_stmt.where(RiskMatrix.project_id == project_id)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(RiskMatrix.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/tech_dev/risk_matrices.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "project_id": project_id,
        "page_title": "Risk Matrices",
    })


@router.get("/risk-matrices/table")
async def risk_matrices_table(
    request: Request,
    page: int = 1,
    search: str = "",
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(RiskMatrix).where(RiskMatrix.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(RiskMatrix.__table__).where(RiskMatrix.is_deleted == False)  # noqa: E712

    if search:
        flt = RiskMatrix.code.ilike(f"%{search}%")
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if project_id is not None:
        stmt = stmt.where(RiskMatrix.project_id == project_id)
        count_stmt = count_stmt.where(RiskMatrix.project_id == project_id)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(RiskMatrix.code).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/tech_dev/_risk_matrices_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "project_id": project_id,
    })


@router.get("/risk-matrices/create")
async def create_risk_matrix_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/tech_dev/risk_matrix_create.html", {
        "page_title": "Create Risk Matrix",
    })


@router.get("/risk-matrices/{matrix_id}")
async def detail_risk_matrix(
    request: Request,
    matrix_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(RiskMatrix).where(RiskMatrix.id == matrix_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/risk-matrices")
    return render(request, "pages/tech_dev/risk_matrix_detail.html", {
        "item": item,
        "page_title": f"Risk Matrix {item.code}",
    })


@router.get("/risk-matrices/{matrix_id}/edit")
async def edit_risk_matrix_form(
    request: Request,
    matrix_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(RiskMatrix).where(RiskMatrix.id == matrix_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/risk-matrices")
    return render(request, "pages/tech_dev/risk_matrix_edit.html", {
        "item": item,
        "page_title": f"Edit Risk Matrix {item.code}",
    })


@router.post("/risk-matrices")
async def create_risk_matrix(
    request: Request,
    code: str = Form(...),
    project_id: Optional[int] = Form(None),
    version: str = Form("1.0"),
    risks_json: str = Form("[]"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    risks_data = []
    if risks_json:
        try:
            risks_data = json.loads(risks_json)
        except json.JSONDecodeError:
            risks_data = []

    item = RiskMatrix(
        code=code,
        project_id=project_id,
        version=version,
        risks=risks_data,
    )
    db.add(item)
    await db.commit()
    return _redirect("/development/risk-matrices")


@router.post("/risk-matrices/{matrix_id}/edit")
async def edit_risk_matrix(
    request: Request,
    matrix_id: int,
    risks_json: str = Form("[]"),
    version: str = Form("1.0"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(RiskMatrix).where(RiskMatrix.id == matrix_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/risk-matrices")

    risks_data = []
    if risks_json:
        try:
            risks_data = json.loads(risks_json)
        except json.JSONDecodeError:
            risks_data = []

    item.risks = risks_data
    item.version = version
    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return _redirect(f"/development/risk-matrices/{matrix_id}")


@router.post("/risk-matrices/{matrix_id}/delete")
async def delete_risk_matrix(
    request: Request,
    matrix_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(RiskMatrix).where(RiskMatrix.id == matrix_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/development/risk-matrices")


@router.post("/risk-matrices/{matrix_id}/restore")
async def restore_risk_matrix(
    request: Request,
    matrix_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(RiskMatrix).where(RiskMatrix.id == matrix_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = False
        item.deleted_at = None
        await db.commit()
    return _redirect(f"/development/risk-matrices/{matrix_id}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. QA Test Reports
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/qa-reports")
async def list_qa_reports(
    request: Request,
    page: int = 1,
    search: str = "",
    test_type: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(QATestReport).where(QATestReport.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(QATestReport.__table__).where(QATestReport.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            QATestReport.code.ilike(f"%{search}%"),
            QATestReport.title.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if test_type:
        stmt = stmt.where(QATestReport.test_type == test_type)
        count_stmt = count_stmt.where(QATestReport.test_type == test_type)
    if status:
        stmt = stmt.where(QATestReport.status == status)
        count_stmt = count_stmt.where(QATestReport.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(QATestReport.created_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/tech_dev/qa_reports.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "test_type": test_type,
        "status": status,
        "page_title": "QA Test Reports",
    })


@router.get("/qa-reports/table")
async def qa_reports_table(
    request: Request,
    page: int = 1,
    search: str = "",
    test_type: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(QATestReport).where(QATestReport.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(QATestReport.__table__).where(QATestReport.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            QATestReport.code.ilike(f"%{search}%"),
            QATestReport.title.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if test_type:
        stmt = stmt.where(QATestReport.test_type == test_type)
        count_stmt = count_stmt.where(QATestReport.test_type == test_type)
    if status:
        stmt = stmt.where(QATestReport.status == status)
        count_stmt = count_stmt.where(QATestReport.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(QATestReport.created_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/tech_dev/_qa_reports_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "test_type": test_type,
        "status": status,
    })


@router.get("/qa-reports/create")
async def create_qa_report_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/tech_dev/qa_report_create.html", {
        "page_title": "Create QA Test Report",
    })


@router.get("/qa-reports/{report_id}")
async def detail_qa_report(
    request: Request,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QATestReport).where(QATestReport.id == report_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/qa-reports")

    pass_rate = 0
    if item.total_tests > 0:
        pass_rate = round((item.passed / item.total_tests) * 100, 1)

    return render(request, "pages/tech_dev/qa_report_detail.html", {
        "item": item,
        "pass_rate": pass_rate,
        "page_title": f"QA Report {item.code}",
    })


@router.get("/qa-reports/{report_id}/edit")
async def edit_qa_report_form(
    request: Request,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QATestReport).where(QATestReport.id == report_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/qa-reports")
    return render(request, "pages/tech_dev/qa_report_edit.html", {
        "item": item,
        "page_title": f"Edit QA Report {item.code}",
    })


@router.post("/qa-reports")
async def create_qa_report(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    release_id: Optional[int] = Form(None),
    test_type: str = Form(...),
    total_tests: int = Form(...),
    passed: int = Form(...),
    failed: int = Form(...),
    blocked: int = Form(0),
    report_url: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = QATestReport(
        code=code,
        title=title,
        release_id=release_id,
        test_type=test_type,
        total_tests=total_tests,
        passed=passed,
        failed=failed,
        blocked=blocked,
        report_url=report_url or None,
        status="draft",
    )
    db.add(item)
    await db.commit()
    return _redirect("/development/qa-reports")


@router.post("/qa-reports/{report_id}/edit")
async def edit_qa_report(
    request: Request,
    report_id: int,
    title: str = Form(...),
    total_tests: int = Form(...),
    passed: int = Form(...),
    failed: int = Form(...),
    blocked: int = Form(0),
    report_url: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QATestReport).where(QATestReport.id == report_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/qa-reports")
    item.title = title
    item.total_tests = total_tests
    item.passed = passed
    item.failed = failed
    item.blocked = blocked
    item.report_url = report_url or None
    await db.commit()
    return _redirect(f"/development/qa-reports/{report_id}")


@router.post("/qa-reports/{report_id}/finalize")
async def finalize_qa_report(
    request: Request,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QATestReport).where(QATestReport.id == report_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "final"
        await db.commit()
    return _redirect(f"/development/qa-reports/{report_id}")


@router.post("/qa-reports/{report_id}/delete")
async def delete_qa_report(
    request: Request,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QATestReport).where(QATestReport.id == report_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/development/qa-reports")


@router.post("/qa-reports/{report_id}/restore")
async def restore_qa_report(
    request: Request,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(QATestReport).where(QATestReport.id == report_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = False
        item.deleted_at = None
        await db.commit()
    return _redirect(f"/development/qa-reports/{report_id}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Deployment Records (append-only — no edit)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/deployments")
async def list_deployments(
    request: Request,
    page: int = 1,
    search: str = "",
    environment: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(DeploymentRecord).where(DeploymentRecord.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(DeploymentRecord.__table__).where(DeploymentRecord.is_deleted == False)  # noqa: E712

    if search:
        flt = DeploymentRecord.code.ilike(f"%{search}%")
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if environment:
        stmt = stmt.where(DeploymentRecord.environment == environment)
        count_stmt = count_stmt.where(DeploymentRecord.environment == environment)
    if status:
        stmt = stmt.where(DeploymentRecord.status == status)
        count_stmt = count_stmt.where(DeploymentRecord.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(DeploymentRecord.deployed_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/tech_dev/deployments.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "environment": environment,
        "status": status,
        "page_title": "Deployment Records",
    })


@router.get("/deployments/table")
async def deployments_table(
    request: Request,
    page: int = 1,
    search: str = "",
    environment: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(DeploymentRecord).where(DeploymentRecord.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(DeploymentRecord.__table__).where(DeploymentRecord.is_deleted == False)  # noqa: E712

    if search:
        flt = DeploymentRecord.code.ilike(f"%{search}%")
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if environment:
        stmt = stmt.where(DeploymentRecord.environment == environment)
        count_stmt = count_stmt.where(DeploymentRecord.environment == environment)
    if status:
        stmt = stmt.where(DeploymentRecord.status == status)
        count_stmt = count_stmt.where(DeploymentRecord.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(DeploymentRecord.deployed_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/tech_dev/_deployments_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "environment": environment,
        "status": status,
    })


@router.get("/deployments/create")
async def create_deployment_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/tech_dev/deployment_create.html", {
        "page_title": "Create Deployment Record",
    })


@router.get("/deployments/{deployment_id}")
async def detail_deployment(
    request: Request,
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(DeploymentRecord).where(DeploymentRecord.id == deployment_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/deployments")
    return render(request, "pages/tech_dev/deployment_detail.html", {
        "item": item,
        "page_title": f"Deployment {item.code}",
    })


@router.post("/deployments")
async def create_deployment(
    request: Request,
    code: str = Form(...),
    release_id: Optional[int] = Form(None),
    environment: str = Form(...),
    deployed_by: str = Form(...),
    status: str = Form(...),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = DeploymentRecord(
        code=code,
        release_id=release_id,
        environment=environment,
        deployed_by=deployed_by,
        status=status,
        notes=notes or None,
    )
    db.add(item)
    await db.commit()
    return _redirect("/development/deployments")


@router.post("/deployments/{deployment_id}/delete")
async def delete_deployment(
    request: Request,
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(DeploymentRecord).where(DeploymentRecord.id == deployment_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/development/deployments")


@router.post("/deployments/{deployment_id}/restore")
async def restore_deployment(
    request: Request,
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(DeploymentRecord).where(DeploymentRecord.id == deployment_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = False
        item.deleted_at = None
        await db.commit()
    return _redirect(f"/development/deployments/{deployment_id}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. UAT Sign-Offs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/signoffs")
async def list_signoffs(
    request: Request,
    page: int = 1,
    search: str = "",
    release_id: Optional[int] = None,
    project_id: Optional[int] = None,
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(UATSignOff).where(UATSignOff.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(UATSignOff.__table__).where(UATSignOff.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            UATSignOff.code.ilike(f"%{search}%"),
            UATSignOff.signed_by.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if release_id is not None:
        stmt = stmt.where(UATSignOff.release_id == release_id)
        count_stmt = count_stmt.where(UATSignOff.release_id == release_id)
    if project_id is not None:
        stmt = stmt.where(UATSignOff.project_id == project_id)
        count_stmt = count_stmt.where(UATSignOff.project_id == project_id)
    if status:
        stmt = stmt.where(UATSignOff.status == status)
        count_stmt = count_stmt.where(UATSignOff.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(UATSignOff.signed_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/tech_dev/signoffs.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "release_id": release_id,
        "project_id": project_id,
        "status": status,
        "page_title": "UAT Sign-Offs",
    })


@router.get("/signoffs/table")
async def signoffs_table(
    request: Request,
    page: int = 1,
    search: str = "",
    release_id: Optional[int] = None,
    project_id: Optional[int] = None,
    status: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(UATSignOff).where(UATSignOff.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(UATSignOff.__table__).where(UATSignOff.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            UATSignOff.code.ilike(f"%{search}%"),
            UATSignOff.signed_by.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if release_id is not None:
        stmt = stmt.where(UATSignOff.release_id == release_id)
        count_stmt = count_stmt.where(UATSignOff.release_id == release_id)
    if project_id is not None:
        stmt = stmt.where(UATSignOff.project_id == project_id)
        count_stmt = count_stmt.where(UATSignOff.project_id == project_id)
    if status:
        stmt = stmt.where(UATSignOff.status == status)
        count_stmt = count_stmt.where(UATSignOff.status == status)

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(UATSignOff.signed_at.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/tech_dev/_signoffs_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "release_id": release_id,
        "project_id": project_id,
        "status": status,
    })


@router.get("/signoffs/create")
async def create_signoff_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/tech_dev/signoff_create.html", {
        "page_title": "Create UAT Sign-Off",
    })


@router.get("/signoffs/{signoff_id}")
async def detail_signoff(
    request: Request,
    signoff_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/signoffs")
    return render(request, "pages/tech_dev/signoff_detail.html", {
        "item": item,
        "page_title": f"Sign-Off {item.code}",
    })


@router.get("/signoffs/{signoff_id}/edit")
async def edit_signoff_form(
    request: Request,
    signoff_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/signoffs")
    return render(request, "pages/tech_dev/signoff_edit.html", {
        "item": item,
        "page_title": f"Edit Sign-Off {item.code}",
    })


@router.post("/signoffs")
async def create_signoff(
    request: Request,
    code: str = Form(...),
    release_id: Optional[int] = Form(None),
    project_id: Optional[int] = Form(None),
    signed_by: str = Form(...),
    comments: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = UATSignOff(
        code=code,
        release_id=release_id,
        project_id=project_id,
        signed_by=signed_by,
        comments=comments or None,
        status="pending",
    )
    db.add(item)
    await db.commit()
    return _redirect("/development/signoffs")


@router.post("/signoffs/{signoff_id}/edit")
async def edit_signoff(
    request: Request,
    signoff_id: int,
    comments: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/signoffs")
    item.comments = comments or None
    await db.commit()
    return _redirect(f"/development/signoffs/{signoff_id}")


@router.post("/signoffs/{signoff_id}/sign")
async def sign_signoff(
    request: Request,
    signoff_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "signed"
        await db.commit()
    return _redirect(f"/development/signoffs/{signoff_id}")


@router.post("/signoffs/{signoff_id}/reject")
async def reject_signoff(
    request: Request,
    signoff_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "rejected"
        await db.commit()
    return _redirect(f"/development/signoffs/{signoff_id}")


@router.post("/signoffs/{signoff_id}/delete")
async def delete_signoff(
    request: Request,
    signoff_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/development/signoffs")


@router.post("/signoffs/{signoff_id}/restore")
async def restore_signoff(
    request: Request,
    signoff_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = False
        item.deleted_at = None
        await db.commit()
    return _redirect(f"/development/signoffs/{signoff_id}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. Solution Sunsets
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/sunsets")
async def list_sunsets(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    product: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(SolutionSunset).where(SolutionSunset.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(SolutionSunset.__table__).where(SolutionSunset.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            SolutionSunset.code.ilike(f"%{search}%"),
            SolutionSunset.product.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if status:
        stmt = stmt.where(SolutionSunset.status == status)
        count_stmt = count_stmt.where(SolutionSunset.status == status)
    if product:
        stmt = stmt.where(SolutionSunset.product.ilike(f"%{product}%"))
        count_stmt = count_stmt.where(SolutionSunset.product.ilike(f"%{product}%"))

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(SolutionSunset.sunset_date.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "pages/tech_dev/sunsets.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "status": status,
        "product": product,
        "page_title": "Solution Sunsets",
    })


@router.get("/sunsets/table")
async def sunsets_table(
    request: Request,
    page: int = 1,
    search: str = "",
    status: str = "",
    product: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    stmt = select(SolutionSunset).where(SolutionSunset.is_deleted == False)  # noqa: E712
    count_stmt = select(func.count()).select_from(SolutionSunset.__table__).where(SolutionSunset.is_deleted == False)  # noqa: E712

    if search:
        flt = or_(
            SolutionSunset.code.ilike(f"%{search}%"),
            SolutionSunset.product.ilike(f"%{search}%"),
        )
        stmt = stmt.where(flt)
        count_stmt = count_stmt.where(flt)
    if status:
        stmt = stmt.where(SolutionSunset.status == status)
        count_stmt = count_stmt.where(SolutionSunset.status == status)
    if product:
        stmt = stmt.where(SolutionSunset.product.ilike(f"%{product}%"))
        count_stmt = count_stmt.where(SolutionSunset.product.ilike(f"%{product}%"))

    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    stmt = stmt.order_by(SolutionSunset.sunset_date.desc()).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return render(request, "partials/tech_dev/_sunsets_table.html", {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "status": status,
        "product": product,
    })


@router.get("/sunsets/create")
async def create_sunset_form(
    request: Request,
    user=Depends(get_current_user_from_session),
):
    return render(request, "pages/tech_dev/sunset_create.html", {
        "page_title": "Create Solution Sunset",
    })


@router.get("/sunsets/{sunset_id}")
async def detail_sunset(
    request: Request,
    sunset_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/sunsets")
    return render(request, "pages/tech_dev/sunset_detail.html", {
        "item": item,
        "page_title": f"Sunset {item.code}",
    })


@router.get("/sunsets/{sunset_id}/edit")
async def edit_sunset_form(
    request: Request,
    sunset_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/sunsets")
    return render(request, "pages/tech_dev/sunset_edit.html", {
        "item": item,
        "page_title": f"Edit Sunset {item.code}",
    })


@router.post("/sunsets")
async def create_sunset(
    request: Request,
    code: str = Form(...),
    product: str = Form(...),
    sunset_date: date = Form(...),
    migration_path: str = Form(...),
    approved_by: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    item = SolutionSunset(
        code=code,
        product=product,
        sunset_date=sunset_date,
        migration_path=migration_path,
        approved_by=approved_by,
        status="planned",
    )
    db.add(item)
    await db.commit()
    return _redirect("/development/sunsets")


@router.post("/sunsets/{sunset_id}/edit")
async def edit_sunset(
    request: Request,
    sunset_id: int,
    product: str = Form(...),
    sunset_date: date = Form(...),
    migration_path: str = Form(...),
    approved_by: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    item = result.scalar_one_or_none()
    if not item:
        return _redirect("/development/sunsets")
    item.product = product
    item.sunset_date = sunset_date
    item.migration_path = migration_path
    item.approved_by = approved_by
    await db.commit()
    return _redirect(f"/development/sunsets/{sunset_id}")


@router.post("/sunsets/{sunset_id}/start")
async def start_sunset(
    request: Request,
    sunset_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "in_progress"
        await db.commit()
    return _redirect(f"/development/sunsets/{sunset_id}")


@router.post("/sunsets/{sunset_id}/complete")
async def complete_sunset(
    request: Request,
    sunset_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = "completed"
        await db.commit()
    return _redirect(f"/development/sunsets/{sunset_id}")


@router.post("/sunsets/{sunset_id}/delete")
async def delete_sunset(
    request: Request,
    sunset_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    return _redirect("/development/sunsets")


@router.post("/sunsets/{sunset_id}/restore")
async def restore_sunset(
    request: Request,
    sunset_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    item = result.scalar_one_or_none()
    if item:
        item.is_deleted = False
        item.deleted_at = None
        await db.commit()
    return _redirect(f"/development/sunsets/{sunset_id}")
