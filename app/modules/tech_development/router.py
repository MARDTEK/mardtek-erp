"""P4 — Design & Development of Solutions: FastAPI routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.modules.tech_development.domain.logic import (
    calculate_qa_pass_rate,
    create_deployment_record,
    get_active_roadmap_items,
    get_release_by_status,
)
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
from app.modules.tech_development.schemas.dto import (
    DeploymentRecordCreate,
    DeploymentRecordResponse,
    ProductRoadmapCreate,
    ProductRoadmapResponse,
    ProductRoadmapUpdate,
    QATestReportCreate,
    QATestReportResponse,
    QATestReportUpdate,
    ReleasePlanCreate,
    ReleasePlanResponse,
    ReleasePlanUpdate,
    RiskMatrixCreate,
    RiskMatrixResponse,
    RiskMatrixUpdate,
    SolutionSunsetCreate,
    SolutionSunsetResponse,
    SolutionSunsetUpdate,
    TechnicalSpecificationCreate,
    TechnicalSpecificationResponse,
    TechnicalSpecificationUpdate,
    UATSignOffCreate,
    UATSignOffResponse,
    UATSignOffUpdate,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# ─── ProductRoadmap (PLN-P4-001) ──────────────────────────────────────────


@router.get("/roadmaps", response_model=List[ProductRoadmapResponse])
async def list_roadmaps(
    product_line: str | None = None,
    year: int | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ProductRoadmap)
    if product_line:
        stmt = stmt.where(ProductRoadmap.product_line == product_line)
    if year is not None:
        stmt = stmt.where(ProductRoadmap.year == year)
    if status:
        stmt = stmt.where(ProductRoadmap.status == status)
    result = await db.execute(stmt.order_by(ProductRoadmap.year.desc()))
    return list(result.scalars().all())


@router.post("/roadmaps", response_model=ProductRoadmapResponse, status_code=status.HTTP_201_CREATED)
async def create_roadmap(payload: ProductRoadmapCreate, db: AsyncSession = Depends(get_db)):
    roadmap = ProductRoadmap(**payload.model_dump())
    db.add(roadmap)
    await db.flush()
    return roadmap


@router.get("/roadmaps/{roadmap_id}", response_model=ProductRoadmapResponse)
async def get_roadmap(roadmap_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductRoadmap).where(ProductRoadmap.id == roadmap_id))
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return roadmap


@router.patch("/roadmaps/{roadmap_id}", response_model=ProductRoadmapResponse)
async def update_roadmap(roadmap_id: int, payload: ProductRoadmapUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductRoadmap).where(ProductRoadmap.id == roadmap_id))
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(roadmap, field, value)
    await db.flush()
    return roadmap


@router.delete("/roadmaps/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_roadmap(roadmap_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductRoadmap).where(ProductRoadmap.id == roadmap_id))
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    await db.delete(roadmap)
    await db.flush()


# ─── ReleasePlan (PLN-P4-002) ─────────────────────────────────────────────


@router.get("/releases", response_model=List[ReleasePlanResponse])
async def list_releases(
    status: str | None = None,
    product: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if status:
        return await get_release_by_status(db, status)

    stmt = select(ReleasePlan)
    if product:
        stmt = stmt.where(ReleasePlan.product == product)
    result = await db.execute(stmt.order_by(ReleasePlan.planned_date.desc()))
    return list(result.scalars().all())


@router.post("/releases", response_model=ReleasePlanResponse, status_code=status.HTTP_201_CREATED)
async def create_release(payload: ReleasePlanCreate, db: AsyncSession = Depends(get_db)):
    release = ReleasePlan(**payload.model_dump())
    db.add(release)
    await db.flush()
    return release


@router.get("/releases/{release_id}", response_model=ReleasePlanResponse)
async def get_release(release_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Release plan not found")
    return release


@router.patch("/releases/{release_id}", response_model=ReleasePlanResponse)
async def update_release(release_id: int, payload: ReleasePlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Release plan not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(release, field, value)
    await db.flush()
    return release


@router.delete("/releases/{release_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_release(release_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReleasePlan).where(ReleasePlan.id == release_id))
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Release plan not found")
    await db.delete(release)
    await db.flush()


# ─── TechnicalSpecification ───────────────────────────────────────────────


@router.get("/specifications", response_model=List[TechnicalSpecificationResponse])
async def list_specifications(
    project_id: int | None = None,
    product: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(TechnicalSpecification)
    if project_id is not None:
        stmt = stmt.where(TechnicalSpecification.project_id == project_id)
    if product:
        stmt = stmt.where(TechnicalSpecification.product == product)
    if status:
        stmt = stmt.where(TechnicalSpecification.status == status)
    result = await db.execute(stmt.order_by(TechnicalSpecification.code))
    return list(result.scalars().all())


@router.post("/specifications", response_model=TechnicalSpecificationResponse, status_code=status.HTTP_201_CREATED)
async def create_specification(payload: TechnicalSpecificationCreate, db: AsyncSession = Depends(get_db)):
    spec = TechnicalSpecification(**payload.model_dump())
    db.add(spec)
    await db.flush()
    return spec


@router.get("/specifications/{spec_id}", response_model=TechnicalSpecificationResponse)
async def get_specification(spec_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    spec = result.scalar_one_or_none()
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    return spec


@router.patch("/specifications/{spec_id}", response_model=TechnicalSpecificationResponse)
async def update_specification(
    spec_id: int,
    payload: TechnicalSpecificationUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    spec = result.scalar_one_or_none()
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(spec, field, value)
    await db.flush()
    return spec


@router.delete("/specifications/{spec_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_specification(spec_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TechnicalSpecification).where(TechnicalSpecification.id == spec_id))
    spec = result.scalar_one_or_none()
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    await db.delete(spec)
    await db.flush()


# ─── RiskMatrix (MAT-P4-001) ──────────────────────────────────────────────


@router.get("/risk-matrices", response_model=List[RiskMatrixResponse])
async def list_risk_matrices(
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(RiskMatrix)
    if project_id is not None:
        stmt = stmt.where(RiskMatrix.project_id == project_id)
    result = await db.execute(stmt.order_by(RiskMatrix.code))
    return list(result.scalars().all())


@router.post("/risk-matrices", response_model=RiskMatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_risk_matrix(payload: RiskMatrixCreate, db: AsyncSession = Depends(get_db)):
    matrix = RiskMatrix(**payload.model_dump())
    db.add(matrix)
    await db.flush()
    return matrix


@router.get("/risk-matrices/{matrix_id}", response_model=RiskMatrixResponse)
async def get_risk_matrix(matrix_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RiskMatrix).where(RiskMatrix.id == matrix_id))
    matrix = result.scalar_one_or_none()
    if not matrix:
        raise HTTPException(status_code=404, detail="Risk matrix not found")
    return matrix


@router.patch("/risk-matrices/{matrix_id}", response_model=RiskMatrixResponse)
async def update_risk_matrix(
    matrix_id: int,
    payload: RiskMatrixUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RiskMatrix).where(RiskMatrix.id == matrix_id))
    matrix = result.scalar_one_or_none()
    if not matrix:
        raise HTTPException(status_code=404, detail="Risk matrix not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(matrix, field, value)
    await db.flush()
    return matrix


@router.delete("/risk-matrices/{matrix_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_risk_matrix(matrix_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RiskMatrix).where(RiskMatrix.id == matrix_id))
    matrix = result.scalar_one_or_none()
    if not matrix:
        raise HTTPException(status_code=404, detail="Risk matrix not found")
    await db.delete(matrix)
    await db.flush()


# ─── QATestReport (INF-P4-001) ────────────────────────────────────────────


@router.get("/qa-reports", response_model=List[QATestReportResponse])
async def list_qa_reports(
    test_type: str | None = None,
    status: str | None = None,
    release_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(QATestReport)
    if test_type:
        stmt = stmt.where(QATestReport.test_type == test_type)
    if status:
        stmt = stmt.where(QATestReport.status == status)
    if release_id is not None:
        stmt = stmt.where(QATestReport.release_id == release_id)
    result = await db.execute(stmt.order_by(QATestReport.created_at.desc()))
    return list(result.scalars().all())


@router.post("/qa-reports", response_model=QATestReportResponse, status_code=status.HTTP_201_CREATED)
async def create_qa_report(payload: QATestReportCreate, db: AsyncSession = Depends(get_db)):
    report = QATestReport(**payload.model_dump())
    db.add(report)
    await db.flush()

    # Event: emit QAFailed when there are test failures
    if report.failed > 0:
        await event_bus.emit(
            Event(
                name="QAFailed",
                payload={
                    "report_id": report.id,
                    "code": report.code,
                    "title": report.title,
                    "failed": report.failed,
                    "total": report.total_tests,
                    "pass_rate": calculate_qa_pass_rate(report),
                },
                source_module="tech_development",
            )
        )

    return report


@router.get("/qa-reports/{report_id}", response_model=QATestReportResponse)
async def get_qa_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QATestReport).where(QATestReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="QA report not found")
    return report


@router.patch("/qa-reports/{report_id}", response_model=QATestReportResponse)
async def update_qa_report(
    report_id: int,
    payload: QATestReportUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QATestReport).where(QATestReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="QA report not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    await db.flush()
    return report


@router.delete("/qa-reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_qa_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QATestReport).where(QATestReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="QA report not found")
    await db.delete(report)
    await db.flush()


# ─── DeploymentRecord (REG-P4-001) ────────────────────────────────────────


@router.get("/deployments", response_model=List[DeploymentRecordResponse])
async def list_deployments(
    environment: str | None = None,
    status: str | None = None,
    release_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DeploymentRecord)
    if environment:
        stmt = stmt.where(DeploymentRecord.environment == environment)
    if status:
        stmt = stmt.where(DeploymentRecord.status == status)
    if release_id is not None:
        stmt = stmt.where(DeploymentRecord.release_id == release_id)
    result = await db.execute(stmt.order_by(DeploymentRecord.deployed_at.desc()))
    return list(result.scalars().all())


@router.post("/deployments", response_model=DeploymentRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(payload: DeploymentRecordCreate, db: AsyncSession = Depends(get_db)):
    record = await create_deployment_record(
        db=db,
        code=payload.code,
        release_id=payload.release_id,
        environment=payload.environment,
        deployed_by=payload.deployed_by,
        status=payload.status,
        notes=payload.notes,
    )

    # Event: emit ReleaseDeployed when a deployment succeeds
    if record.status == "success":
        await event_bus.emit(
            Event(
                name="ReleaseDeployed",
                payload={
                    "deployment_id": record.id,
                    "code": record.code,
                    "release_id": record.release_id,
                    "environment": record.environment,
                    "deployed_by": record.deployed_by,
                },
                source_module="tech_development",
            )
        )

    return record


@router.get("/deployments/{deployment_id}", response_model=DeploymentRecordResponse)
async def get_deployment(deployment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DeploymentRecord).where(DeploymentRecord.id == deployment_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Deployment record not found")
    return record


# ─── UATSignOff (FO-P4-001) ───────────────────────────────────────────────


@router.get("/uat-signoffs", response_model=List[UATSignOffResponse])
async def list_uat_signoffs(
    release_id: int | None = None,
    project_id: int | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UATSignOff)
    if release_id is not None:
        stmt = stmt.where(UATSignOff.release_id == release_id)
    if project_id is not None:
        stmt = stmt.where(UATSignOff.project_id == project_id)
    if status:
        stmt = stmt.where(UATSignOff.status == status)
    result = await db.execute(stmt.order_by(UATSignOff.signed_at.desc()))
    return list(result.scalars().all())


@router.post("/uat-signoffs", response_model=UATSignOffResponse, status_code=status.HTTP_201_CREATED)
async def create_uat_signoff(payload: UATSignOffCreate, db: AsyncSession = Depends(get_db)):
    signoff = UATSignOff(**payload.model_dump())
    db.add(signoff)
    await db.flush()
    return signoff


@router.get("/uat-signoffs/{signoff_id}", response_model=UATSignOffResponse)
async def get_uat_signoff(signoff_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    signoff = result.scalar_one_or_none()
    if not signoff:
        raise HTTPException(status_code=404, detail="UAT sign-off not found")
    return signoff


@router.patch("/uat-signoffs/{signoff_id}", response_model=UATSignOffResponse)
async def update_uat_signoff(
    signoff_id: int,
    payload: UATSignOffUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    signoff = result.scalar_one_or_none()
    if not signoff:
        raise HTTPException(status_code=404, detail="UAT sign-off not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(signoff, field, value)
    await db.flush()
    return signoff


@router.delete("/uat-signoffs/{signoff_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_uat_signoff(signoff_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UATSignOff).where(UATSignOff.id == signoff_id))
    signoff = result.scalar_one_or_none()
    if not signoff:
        raise HTTPException(status_code=404, detail="UAT sign-off not found")
    await db.delete(signoff)
    await db.flush()


# ─── SolutionSunset ───────────────────────────────────────────────────────


@router.get("/sunsets", response_model=List[SolutionSunsetResponse])
async def list_sunsets(
    status: str | None = None,
    product: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SolutionSunset)
    if status:
        stmt = stmt.where(SolutionSunset.status == status)
    if product:
        stmt = stmt.where(SolutionSunset.product == product)
    result = await db.execute(stmt.order_by(SolutionSunset.sunset_date))
    return list(result.scalars().all())


@router.post("/sunsets", response_model=SolutionSunsetResponse, status_code=status.HTTP_201_CREATED)
async def create_sunset(payload: SolutionSunsetCreate, db: AsyncSession = Depends(get_db)):
    sunset = SolutionSunset(**payload.model_dump())
    db.add(sunset)
    await db.flush()
    return sunset


@router.get("/sunsets/{sunset_id}", response_model=SolutionSunsetResponse)
async def get_sunset(sunset_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    sunset = result.scalar_one_or_none()
    if not sunset:
        raise HTTPException(status_code=404, detail="Sunset plan not found")
    return sunset


@router.patch("/sunsets/{sunset_id}", response_model=SolutionSunsetResponse)
async def update_sunset(
    sunset_id: int,
    payload: SolutionSunsetUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    sunset = result.scalar_one_or_none()
    if not sunset:
        raise HTTPException(status_code=404, detail="Sunset plan not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sunset, field, value)
    await db.flush()
    return sunset


@router.delete("/sunsets/{sunset_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_sunset(sunset_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SolutionSunset).where(SolutionSunset.id == sunset_id))
    sunset = result.scalar_one_or_none()
    if not sunset:
        raise HTTPException(status_code=404, detail="Sunset plan not found")
    await db.delete(sunset)
    await db.flush()
