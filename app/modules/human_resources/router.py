from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.modules.human_resources.domain.logic import (
    get_active_headcount,
    get_employees_by_competency_gap,
    get_turnover_rate,
)
from app.modules.human_resources.domain.models import (
    EvaluationStatus,
    IndividualDevelopmentPlan,
    InductionChecklist,
    JobDescription,
    LaborIncident,
    PerformanceEvaluation,
    PersonnelRequest,
    StaffRegister,
)
from app.modules.human_resources.schemas.dto import (
    IndividualDevelopmentPlanCreate,
    IndividualDevelopmentPlanResponse,
    IndividualDevelopmentPlanUpdate,
    InductionChecklistCreate,
    InductionChecklistResponse,
    InductionChecklistUpdate,
    JobDescriptionCreate,
    JobDescriptionResponse,
    JobDescriptionUpdate,
    LaborIncidentCreate,
    LaborIncidentResponse,
    LaborIncidentUpdate,
    PerformanceEvaluationCreate,
    PerformanceEvaluationResponse,
    PerformanceEvaluationUpdate,
    PersonnelRequestCreate,
    PersonnelRequestResponse,
    PersonnelRequestUpdate,
    StaffRegisterCreate,
    StaffRegisterResponse,
    StaffRegisterUpdate,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# ═══════════════════════════════════════════════════════════════════════════
# JOB DESCRIPTIONS (PER-P7-001)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/job-descriptions", response_model=List[JobDescriptionResponse])
async def list_job_descriptions(
    department: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(JobDescription)
    if department:
        stmt = stmt.where(JobDescription.department == department)
    if is_active is not None:
        stmt = stmt.where(JobDescription.is_active == is_active)
    result = await db.execute(stmt.order_by(JobDescription.code))
    return list(result.scalars().all())


@router.post("/job-descriptions", response_model=JobDescriptionResponse, status_code=201)
async def create_job_description(payload: JobDescriptionCreate, db: AsyncSession = Depends(get_db)):
    jd = JobDescription(**payload.model_dump())
    db.add(jd)
    await db.flush()
    return jd


@router.get("/job-descriptions/{jd_id}", response_model=JobDescriptionResponse)
async def get_job_description(jd_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


@router.patch("/job-descriptions/{jd_id}", response_model=JobDescriptionResponse)
async def update_job_description(jd_id: int, payload: JobDescriptionUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(jd, field, value)
    await db.flush()
    return jd


@router.delete("/job-descriptions/{jd_id}", status_code=204, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_job_description(jd_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    await db.delete(jd)
    await db.flush()


# ═══════════════════════════════════════════════════════════════════════════
# PERSONNEL REQUESTS (FO-P7-001)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/personnel-requests", response_model=List[PersonnelRequestResponse])
async def list_personnel_requests(
    department: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PersonnelRequest)
    if department:
        stmt = stmt.where(PersonnelRequest.department == department)
    if status:
        stmt = stmt.where(PersonnelRequest.status == status)
    result = await db.execute(stmt.order_by(PersonnelRequest.created_at.desc()))
    return list(result.scalars().all())


@router.post("/personnel-requests", response_model=PersonnelRequestResponse, status_code=201)
async def create_personnel_request(payload: PersonnelRequestCreate, db: AsyncSession = Depends(get_db)):
    pr = PersonnelRequest(**payload.model_dump())
    db.add(pr)
    await db.flush()
    return pr


@router.get("/personnel-requests/{pr_id}", response_model=PersonnelRequestResponse)
async def get_personnel_request(pr_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PersonnelRequest).where(PersonnelRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Personnel request not found")
    return pr


@router.patch("/personnel-requests/{pr_id}", response_model=PersonnelRequestResponse)
async def update_personnel_request(pr_id: int, payload: PersonnelRequestUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PersonnelRequest).where(PersonnelRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Personnel request not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pr, field, value)
    await db.flush()
    return pr


# ═══════════════════════════════════════════════════════════════════════════
# INDUCTION CHECKLISTS (FO-P7-002)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/induction-checklists", response_model=List[InductionChecklistResponse])
async def list_induction_checklists(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(InductionChecklist)
    if status:
        stmt = stmt.where(InductionChecklist.status == status)
    result = await db.execute(stmt.order_by(InductionChecklist.hire_date.desc()))
    return list(result.scalars().all())


@router.post("/induction-checklists", response_model=InductionChecklistResponse, status_code=201)
async def create_induction_checklist(payload: InductionChecklistCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump()
    data["items"] = [item.model_dump() for item in data.pop("items", [])]
    checklist = InductionChecklist(**data)
    db.add(checklist)
    await db.flush()
    return checklist


@router.get("/induction-checklists/{ic_id}", response_model=InductionChecklistResponse)
async def get_induction_checklist(ic_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InductionChecklist).where(InductionChecklist.id == ic_id))
    ic = result.scalar_one_or_none()
    if not ic:
        raise HTTPException(status_code=404, detail="Induction checklist not found")
    return ic


@router.patch("/induction-checklists/{ic_id}", response_model=InductionChecklistResponse)
async def update_induction_checklist(ic_id: int, payload: InductionChecklistUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InductionChecklist).where(InductionChecklist.id == ic_id))
    ic = result.scalar_one_or_none()
    if not ic:
        raise HTTPException(status_code=404, detail="Induction checklist not found")
    data = payload.model_dump(exclude_unset=True)
    if "items" in data:
        data["items"] = [item.model_dump() for item in data["items"]]
    for field, value in data.items():
        setattr(ic, field, value)
    await db.flush()
    return ic


# ═══════════════════════════════════════════════════════════════════════════
# INDIVIDUAL DEVELOPMENT PLANS (REG-P7-002)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/development-plans", response_model=List[IndividualDevelopmentPlanResponse])
async def list_development_plans(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(IndividualDevelopmentPlan)
    if status:
        stmt = stmt.where(IndividualDevelopmentPlan.status == status)
    result = await db.execute(stmt.order_by(IndividualDevelopmentPlan.review_date.desc().nullslast()))
    return list(result.scalars().all())


@router.post("/development-plans", response_model=IndividualDevelopmentPlanResponse, status_code=201)
async def create_development_plan(payload: IndividualDevelopmentPlanCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump()
    data["goals"] = [g.model_dump() for g in data.pop("goals", [])]
    data["courses"] = [c.model_dump() for c in data.pop("courses", [])]
    plan = IndividualDevelopmentPlan(**data)
    db.add(plan)
    await db.flush()
    return plan


@router.get("/development-plans/{dp_id}", response_model=IndividualDevelopmentPlanResponse)
async def get_development_plan(dp_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IndividualDevelopmentPlan).where(IndividualDevelopmentPlan.id == dp_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Development plan not found")
    return plan


@router.patch("/development-plans/{dp_id}", response_model=IndividualDevelopmentPlanResponse)
async def update_development_plan(dp_id: int, payload: IndividualDevelopmentPlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IndividualDevelopmentPlan).where(IndividualDevelopmentPlan.id == dp_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Development plan not found")
    data = payload.model_dump(exclude_unset=True)
    if "goals" in data:
        data["goals"] = [g.model_dump() for g in data["goals"]]
    if "courses" in data:
        data["courses"] = [c.model_dump() for c in data["courses"]]
    for field, value in data.items():
        setattr(plan, field, value)
    await db.flush()
    return plan


# ═══════════════════════════════════════════════════════════════════════════
# PERFORMANCE EVALUATIONS (FO-P7-003)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/evaluations", response_model=List[PerformanceEvaluationResponse])
async def list_evaluations(
    employee_name: str | None = None,
    status: str | None = None,
    period: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PerformanceEvaluation)
    if employee_name:
        stmt = stmt.where(PerformanceEvaluation.employee_name.ilike(f"%{employee_name}%"))
    if status:
        stmt = stmt.where(PerformanceEvaluation.status == status)
    if period:
        stmt = stmt.where(PerformanceEvaluation.period == period)
    result = await db.execute(stmt.order_by(PerformanceEvaluation.created_at.desc()))
    return list(result.scalars().all())


@router.post("/evaluations", response_model=PerformanceEvaluationResponse, status_code=201)
async def create_evaluation(payload: PerformanceEvaluationCreate, db: AsyncSession = Depends(get_db)):
    evaluation = PerformanceEvaluation(**payload.model_dump())
    db.add(evaluation)
    await db.flush()
    return evaluation


@router.get("/evaluations/{eval_id}", response_model=PerformanceEvaluationResponse)
async def get_evaluation(eval_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PerformanceEvaluation).where(PerformanceEvaluation.id == eval_id))
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.patch("/evaluations/{eval_id}", response_model=PerformanceEvaluationResponse)
async def update_evaluation(eval_id: int, payload: PerformanceEvaluationUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PerformanceEvaluation).where(PerformanceEvaluation.id == eval_id))
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(evaluation, field, value)
    await db.flush()

    # Emit event when evaluation reaches completed
    if evaluation.status == EvaluationStatus.COMPLETED:
        await event_bus.emit(Event(
            name="PerformanceReviewCompleted",
            payload={
                "evaluation_id": evaluation.id,
                "employee_name": evaluation.employee_name,
                "evaluator": evaluation.evaluator,
                "period": evaluation.period,
                "score": evaluation.score,
            },
            source_module="human_resources",
        ))

    return evaluation


# ═══════════════════════════════════════════════════════════════════════════
# LABOR INCIDENTS (FO-P7-004)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/labor-incidents", response_model=List[LaborIncidentResponse])
async def list_labor_incidents(
    incident_type: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LaborIncident)
    if incident_type:
        stmt = stmt.where(LaborIncident.incident_type == incident_type)
    if status:
        stmt = stmt.where(LaborIncident.status == status)
    result = await db.execute(stmt.order_by(LaborIncident.created_at.desc()))
    return list(result.scalars().all())


@router.post("/labor-incidents", response_model=LaborIncidentResponse, status_code=201)
async def create_labor_incident(payload: LaborIncidentCreate, db: AsyncSession = Depends(get_db)):
    incident = LaborIncident(**payload.model_dump())
    db.add(incident)
    await db.flush()
    return incident


@router.get("/labor-incidents/{incident_id}", response_model=LaborIncidentResponse)
async def get_labor_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LaborIncident).where(LaborIncident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Labor incident not found")
    return incident


@router.patch("/labor-incidents/{incident_id}", response_model=LaborIncidentResponse)
async def update_labor_incident(incident_id: int, payload: LaborIncidentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LaborIncident).where(LaborIncident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Labor incident not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    await db.flush()
    return incident


# ═══════════════════════════════════════════════════════════════════════════
# STAFF REGISTER (REG-P7-001)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/staff", response_model=List[StaffRegisterResponse])
async def list_staff(
    department: str | None = None,
    status: str | None = None,
    contract_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(StaffRegister)
    if department:
        stmt = stmt.where(StaffRegister.department == department)
    if status:
        stmt = stmt.where(StaffRegister.status == status)
    if contract_type:
        stmt = stmt.where(StaffRegister.contract_type == contract_type)
    result = await db.execute(stmt.order_by(StaffRegister.employee_name))
    return list(result.scalars().all())


@router.post("/staff", response_model=StaffRegisterResponse, status_code=201)
async def create_staff_entry(payload: StaffRegisterCreate, db: AsyncSession = Depends(get_db)):
    entry = StaffRegister(**payload.model_dump())
    db.add(entry)
    await db.flush()

    # Emit PersonnelHired event
    await event_bus.emit(Event(
        name="PersonnelHired",
        payload={
            "staff_id": entry.id,
            "employee_name": entry.employee_name,
            "email": entry.email,
            "department": entry.department,
            "position": entry.position,
            "contract_type": entry.contract_type,
        },
        source_module="human_resources",
    ))

    return entry


@router.get("/staff/{staff_id}", response_model=StaffRegisterResponse)
async def get_staff_entry(staff_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffRegister).where(StaffRegister.id == staff_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Staff entry not found")
    return entry


@router.patch("/staff/{staff_id}", response_model=StaffRegisterResponse)
async def update_staff_entry(staff_id: int, payload: StaffRegisterUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffRegister).where(StaffRegister.id == staff_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Staff entry not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    await db.flush()
    return entry


@router.delete("/staff/{staff_id}", status_code=204, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_staff_entry(staff_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffRegister).where(StaffRegister.id == staff_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Staff entry not found")
    await db.delete(entry)
    await db.flush()


# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN LOGIC ENDPOINTS (analytics / operational queries)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/analytics/headcount")
async def headcount_endpoint(
    department: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    count = await get_active_headcount(db, department)
    return {"department": department, "active_headcount": count}


@router.get("/analytics/turnover-rate")
async def turnover_endpoint(
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    rate = await get_turnover_rate(db, year)
    return {"year": year, "turnover_rate": rate}


@router.get("/analytics/competency-gap")
async def competency_gap_endpoint(
    skill: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    employees = await get_employees_by_competency_gap(db, skill)
    return {"skill": skill, "employees_with_gap": [
        {
            "id": e.id,
            "employee_name": e.employee_name,
            "department": e.department,
            "position": e.position,
        }
        for e in employees
    ]}
