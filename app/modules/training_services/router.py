"""P6 — Training & Human Development: FastAPI routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.core.pagination import PaginationParams, paginate
from app.modules.training_services.domain.logic import (
    calculate_training_effectiveness,
    get_certifications_by_participant,
    update_competency_gap,
)
from app.modules.training_services.domain.models import (
    AttendanceRecord,
    CertificationRecord,
    CompetencyMatrix,
    Course,
    SessionStatus,
    TrainingEvaluation,
    TrainingNeedsAssessment,
    TrainingPlan,
    TrainingSession,
    UserManual,
    VideoTutorial,
)
from app.modules.training_services.schemas.dto import (
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    AttendanceRecordUpdate,
    CertificationRecordCreate,
    CertificationRecordResponse,
    CertificationRecordUpdate,
    CompetencyMatrixCreate,
    CompetencyMatrixGapUpdate,
    CompetencyMatrixResponse,
    CompetencyMatrixUpdate,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    TrainingEffectivenessResponse,
    TrainingEvaluationCreate,
    TrainingEvaluationResponse,
    TrainingEvaluationUpdate,
    TrainingNeedsCreate,
    TrainingNeedsResponse,
    TrainingNeedsUpdate,
    TrainingPlanCreate,
    TrainingPlanResponse,
    TrainingPlanUpdate,
    TrainingSessionCreate,
    TrainingSessionResponse,
    TrainingSessionUpdate,
    UserManualCreate,
    UserManualResponse,
    UserManualUpdate,
    VideoTutorialCreate,
    VideoTutorialResponse,
    VideoTutorialUpdate,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# ─── Training Needs Assessment (FO-P6-001) ───────────────────────────────

@router.get("/needs", response_model=List[TrainingNeedsResponse])
async def list_needs(
    priority: str | None = None,
    status_filter: str | None = None,
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(TrainingNeedsAssessment).where(TrainingNeedsAssessment.is_deleted == False)
    if priority:
        stmt = stmt.where(TrainingNeedsAssessment.priority == priority)
    if status_filter:
        stmt = stmt.where(TrainingNeedsAssessment.status == status_filter)
    if role:
        stmt = stmt.where(TrainingNeedsAssessment.role.ilike(f"%{role}%"))
    result = await db.execute(paginate(stmt.order_by(TrainingNeedsAssessment.code), page))
    return list(result.scalars().all())


@router.post("/needs", response_model=TrainingNeedsResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_need(payload: TrainingNeedsCreate, db: AsyncSession = Depends(get_db)):
    need = TrainingNeedsAssessment(**payload.model_dump())
    db.add(need)
    await db.flush()
    return need


@router.get("/needs/{need_id}", response_model=TrainingNeedsResponse)
async def get_need(need_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingNeedsAssessment).where(TrainingNeedsAssessment.id == need_id, TrainingNeedsAssessment.is_deleted == False)
    )
    need = result.scalar_one_or_none()
    if not need:
        raise HTTPException(status_code=404, detail="Training needs assessment not found")
    return need


@router.patch("/needs/{need_id}", response_model=TrainingNeedsResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_need(need_id: int, payload: TrainingNeedsUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingNeedsAssessment).where(TrainingNeedsAssessment.id == need_id, TrainingNeedsAssessment.is_deleted == False)
    )
    need = result.scalar_one_or_none()
    if not need:
        raise HTTPException(status_code=404, detail="Training needs assessment not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(need, field, value)
    await db.flush()
    return need


@router.delete("/needs/{need_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_need(need_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingNeedsAssessment).where(TrainingNeedsAssessment.id == need_id))
    need = result.scalar_one_or_none()
    if not need or need.is_deleted:
        raise HTTPException(status_code=404, detail="Training needs assessment not found")
    need.is_deleted = True
    need.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Training needs assessment deleted successfully", "id": need_id}


@router.patch("/needs/{need_id}/restore")
async def restore_need(need_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingNeedsAssessment).where(TrainingNeedsAssessment.id == need_id))
    need = result.scalar_one_or_none()
    if not need:
        raise HTTPException(status_code=404, detail="Training needs assessment not found")
    if not need.is_deleted:
        raise HTTPException(status_code=400, detail="Training needs assessment is not deleted")
    need.is_deleted = False
    need.deleted_at = None
    await db.commit()
    return need


# ─── Competency Matrix (MAT-P6-001) ──────────────────────────────────────

@router.get("/competency-matrices", response_model=List[CompetencyMatrixResponse])
async def list_competency_matrices(
    role: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(CompetencyMatrix).where(CompetencyMatrix.is_deleted == False)
    if role:
        stmt = stmt.where(CompetencyMatrix.role.ilike(f"%{role}%"))
    if is_active is not None:
        stmt = stmt.where(CompetencyMatrix.is_active == is_active)
    result = await db.execute(paginate(stmt.order_by(CompetencyMatrix.code), page))
    return list(result.scalars().all())


@router.post("/competency-matrices", response_model=CompetencyMatrixResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_competency_matrix(payload: CompetencyMatrixCreate, db: AsyncSession = Depends(get_db)):
    matrix = CompetencyMatrix(**payload.model_dump())
    db.add(matrix)
    await db.flush()
    return matrix


@router.get("/competency-matrices/{matrix_id}", response_model=CompetencyMatrixResponse)
async def get_competency_matrix(matrix_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CompetencyMatrix).where(CompetencyMatrix.id == matrix_id, CompetencyMatrix.is_deleted == False)
    )
    matrix = result.scalar_one_or_none()
    if not matrix:
        raise HTTPException(status_code=404, detail="Competency matrix not found")
    return matrix


@router.patch("/competency-matrices/{matrix_id}", response_model=CompetencyMatrixResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_competency_matrix(
    matrix_id: int,
    payload: CompetencyMatrixUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompetencyMatrix).where(CompetencyMatrix.id == matrix_id, CompetencyMatrix.is_deleted == False)
    )
    matrix = result.scalar_one_or_none()
    if not matrix:
        raise HTTPException(status_code=404, detail="Competency matrix not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(matrix, field, value)
    await db.flush()
    return matrix


@router.delete("/competency-matrices/{matrix_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_competency_matrix(matrix_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompetencyMatrix).where(CompetencyMatrix.id == matrix_id))
    matrix = result.scalar_one_or_none()
    if not matrix or matrix.is_deleted:
        raise HTTPException(status_code=404, detail="Competency matrix not found")
    matrix.is_deleted = True
    matrix.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Competency matrix deleted successfully", "id": matrix_id}


@router.patch("/competency-matrices/{matrix_id}/restore")
async def restore_competency_matrix(matrix_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompetencyMatrix).where(CompetencyMatrix.id == matrix_id))
    matrix = result.scalar_one_or_none()
    if not matrix:
        raise HTTPException(status_code=404, detail="Competency matrix not found")
    if not matrix.is_deleted:
        raise HTTPException(status_code=400, detail="Competency matrix is not deleted")
    matrix.is_deleted = False
    matrix.deleted_at = None
    await db.commit()
    return matrix


@router.post(
    "/competency-matrices/{matrix_id}/update-gap",
    response_model=CompetencyMatrixResponse,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def update_gap_endpoint(
    matrix_id: int,
    payload: CompetencyMatrixGapUpdate,
    db: AsyncSession = Depends(get_db),
):
    matrix = await update_competency_gap(db, matrix_id, payload.role, payload.competencies)
    if not matrix:
        raise HTTPException(status_code=404, detail="Competency matrix not found")
    return matrix


# ─── Course (SOP-P6-002) ─────────────────────────────────────────────────

@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(
    modality: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(Course).where(Course.is_deleted == False)
    if modality:
        stmt = stmt.where(Course.modality == modality)
    if status_filter:
        stmt = stmt.where(Course.status == status_filter)
    result = await db.execute(paginate(stmt.order_by(Course.code), page))
    return list(result.scalars().all())


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_course(payload: CourseCreate, db: AsyncSession = Depends(get_db)):
    course = Course(**payload.model_dump())
    db.add(course)
    await db.flush()
    return course


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id, Course.is_deleted == False))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.patch("/courses/{course_id}", response_model=CourseResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_course(course_id: int, payload: CourseUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id, Course.is_deleted == False))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    await db.flush()
    return course


@router.delete("/courses/{course_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course or course.is_deleted:
        raise HTTPException(status_code=404, detail="Course not found")
    course.is_deleted = True
    course.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Course deleted successfully", "id": course_id}


@router.patch("/courses/{course_id}/restore")
async def restore_course(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.is_deleted:
        raise HTTPException(status_code=400, detail="Course is not deleted")
    course.is_deleted = False
    course.deleted_at = None
    await db.commit()
    return course


# ─── Training Plan (PLN-P6-001) ──────────────────────────────────────────

@router.get("/plans", response_model=List[TrainingPlanResponse])
async def list_plans(
    year: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(TrainingPlan).where(TrainingPlan.is_deleted == False)
    if year:
        stmt = stmt.where(TrainingPlan.year == year)
    if status_filter:
        stmt = stmt.where(TrainingPlan.status == status_filter)
    result = await db.execute(paginate(stmt.order_by(TrainingPlan.year.desc()), page))
    return list(result.scalars().all())


@router.post("/plans", response_model=TrainingPlanResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_plan(payload: TrainingPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = TrainingPlan(**payload.model_dump())
    db.add(plan)
    await db.flush()
    return plan


@router.get("/plans/{plan_id}", response_model=TrainingPlanResponse)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id, TrainingPlan.is_deleted == False))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    return plan


@router.patch("/plans/{plan_id}", response_model=TrainingPlanResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_plan(plan_id: int, payload: TrainingPlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id, TrainingPlan.is_deleted == False))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.flush()
    return plan


@router.delete("/plans/{plan_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan or plan.is_deleted:
        raise HTTPException(status_code=404, detail="Training plan not found")
    plan.is_deleted = True
    plan.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Training plan deleted successfully", "id": plan_id}


@router.patch("/plans/{plan_id}/restore")
async def restore_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    if not plan.is_deleted:
        raise HTTPException(status_code=400, detail="Training plan is not deleted")
    plan.is_deleted = False
    plan.deleted_at = None
    await db.commit()
    return plan


# ─── Training Session (SOP-P6-003) ───────────────────────────────────────

@router.get("/sessions", response_model=List[TrainingSessionResponse])
async def list_sessions(
    course_id: int | None = None,
    status_filter: str | None = None,
    instructor: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(TrainingSession).where(TrainingSession.is_deleted == False)
    if course_id is not None:
        stmt = stmt.where(TrainingSession.course_id == course_id)
    if status_filter:
        stmt = stmt.where(TrainingSession.status == status_filter)
    if instructor:
        stmt = stmt.where(TrainingSession.instructor.ilike(f"%{instructor}%"))
    result = await db.execute(paginate(stmt.order_by(TrainingSession.start_date.desc()), page))
    return list(result.scalars().all())


@router.post("/sessions", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_session(payload: TrainingSessionCreate, db: AsyncSession = Depends(get_db)):
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == payload.course_id, Course.is_deleted == False))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    session = TrainingSession(**payload.model_dump())
    db.add(session)
    await db.flush()
    return session


@router.get("/sessions/{session_id}", response_model=TrainingSessionResponse)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingSession).where(TrainingSession.id == session_id, TrainingSession.is_deleted == False)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Training session not found")
    return session


@router.patch("/sessions/{session_id}", response_model=TrainingSessionResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_session(
    session_id: int,
    payload: TrainingSessionUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingSession).where(TrainingSession.id == session_id, TrainingSession.is_deleted == False)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Training session not found")

    old_status = session.status
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    await db.flush()

    # Event: emit TrainingCompleted when session reaches completed
    if old_status != SessionStatus.COMPLETED and session.status == SessionStatus.COMPLETED:
        await event_bus.emit(
            Event(
                name="TrainingCompleted",
                payload={
                    "session_id": session.id,
                    "course_id": session.course_id,
                    "instructor": session.instructor,
                    "start_date": str(session.start_date),
                    "end_date": str(session.end_date),
                    "attendees": session.attendees,
                },
                source_module="training_services",
            )
        )

    return session


@router.delete("/sessions/{session_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingSession).where(TrainingSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session or session.is_deleted:
        raise HTTPException(status_code=404, detail="Training session not found")
    session.is_deleted = True
    session.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Training session deleted successfully", "id": session_id}


@router.patch("/sessions/{session_id}/restore")
async def restore_session(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingSession).where(TrainingSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Training session not found")
    if not session.is_deleted:
        raise HTTPException(status_code=400, detail="Training session is not deleted")
    session.is_deleted = False
    session.deleted_at = None
    await db.commit()
    return session


# ─── Training Evaluation (FO-P6-002) ─────────────────────────────────────

@router.get("/evaluations", response_model=List[TrainingEvaluationResponse])
async def list_evaluations(
    session_id: int | None = None,
    participant: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(TrainingEvaluation).where(TrainingEvaluation.is_deleted == False)
    if session_id is not None:
        stmt = stmt.where(TrainingEvaluation.session_id == session_id)
    if participant:
        stmt = stmt.where(TrainingEvaluation.participant.ilike(f"%{participant}%"))
    result = await db.execute(paginate(stmt.order_by(TrainingEvaluation.submitted_at.desc()), page))
    return list(result.scalars().all())


@router.post("/evaluations", response_model=TrainingEvaluationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_evaluation(payload: TrainingEvaluationCreate, db: AsyncSession = Depends(get_db)):
    # Verify session exists
    session_result = await db.execute(
        select(TrainingSession).where(TrainingSession.id == payload.session_id, TrainingSession.is_deleted == False)
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Training session not found")

    evaluation = TrainingEvaluation(**payload.model_dump())
    db.add(evaluation)
    await db.flush()
    return evaluation


@router.patch("/evaluations/{evaluation_id}", response_model=TrainingEvaluationResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_evaluation(
    evaluation_id: int,
    payload: TrainingEvaluationUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingEvaluation).where(TrainingEvaluation.id == evaluation_id, TrainingEvaluation.is_deleted == False)
    )
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Training evaluation not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(evaluation, field, value)
    await db.flush()
    return evaluation


@router.delete("/evaluations/{evaluation_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_evaluation(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingEvaluation).where(TrainingEvaluation.id == evaluation_id))
    evaluation = result.scalar_one_or_none()
    if not evaluation or evaluation.is_deleted:
        raise HTTPException(status_code=404, detail="Training evaluation not found")
    evaluation.is_deleted = True
    evaluation.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Training evaluation deleted successfully", "id": evaluation_id}


@router.patch("/evaluations/{evaluation_id}/restore")
async def restore_evaluation(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingEvaluation).where(TrainingEvaluation.id == evaluation_id))
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Training evaluation not found")
    if not evaluation.is_deleted:
        raise HTTPException(status_code=400, detail="Training evaluation is not deleted")
    evaluation.is_deleted = False
    evaluation.deleted_at = None
    await db.commit()
    return evaluation


# ─── Attendance Record (REG-P6-001) ──────────────────────────────────────

@router.get("/attendance", response_model=List[AttendanceRecordResponse])
async def list_attendance(
    session_id: int | None = None,
    participant_name: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(AttendanceRecord).where(AttendanceRecord.is_deleted == False)
    if session_id is not None:
        stmt = stmt.where(AttendanceRecord.session_id == session_id)
    if participant_name:
        stmt = stmt.where(AttendanceRecord.participant_name.ilike(f"%{participant_name}%"))
    result = await db.execute(paginate(stmt.order_by(AttendanceRecord.signed_at.desc()), page))
    return list(result.scalars().all())


@router.post("/attendance", response_model=AttendanceRecordResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_attendance(payload: AttendanceRecordCreate, db: AsyncSession = Depends(get_db)):
    # Verify session exists
    session_result = await db.execute(
        select(TrainingSession).where(TrainingSession.id == payload.session_id, TrainingSession.is_deleted == False)
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Training session not found")

    record = AttendanceRecord(**payload.model_dump())
    db.add(record)
    await db.flush()
    return record


@router.get("/attendance/{record_id}", response_model=AttendanceRecordResponse)
async def get_attendance(record_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.id == record_id, AttendanceRecord.is_deleted == False)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record


@router.patch("/attendance/{record_id}", response_model=AttendanceRecordResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_attendance(
    record_id: int,
    payload: AttendanceRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.id == record_id, AttendanceRecord.is_deleted == False)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.flush()
    return record


@router.delete("/attendance/{record_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_attendance(record_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AttendanceRecord).where(AttendanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record or record.is_deleted:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    record.is_deleted = True
    record.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Attendance record deleted successfully", "id": record_id}


@router.patch("/attendance/{record_id}/restore")
async def restore_attendance(record_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AttendanceRecord).where(AttendanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    if not record.is_deleted:
        raise HTTPException(status_code=400, detail="Attendance record is not deleted")
    record.is_deleted = False
    record.deleted_at = None
    await db.commit()
    return record


# ─── Certification Record (REG-P6-002) ───────────────────────────────────

@router.get("/certifications", response_model=List[CertificationRecordResponse])
async def list_certifications(
    participant_name: str | None = None,
    status_filter: str | None = None,
    course_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(CertificationRecord).where(CertificationRecord.is_deleted == False)
    if participant_name:
        stmt = stmt.where(CertificationRecord.participant_name.ilike(f"%{participant_name}%"))
    if status_filter:
        stmt = stmt.where(CertificationRecord.status == status_filter)
    if course_id is not None:
        stmt = stmt.where(CertificationRecord.course_id == course_id)
    result = await db.execute(paginate(stmt.order_by(CertificationRecord.issued_at.desc()), page))
    return list(result.scalars().all())


@router.post(
    "/certifications",
    response_model=CertificationRecordResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_certification(payload: CertificationRecordCreate, db: AsyncSession = Depends(get_db)):
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == payload.course_id, Course.is_deleted == False))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    cert = CertificationRecord(**payload.model_dump())
    db.add(cert)
    await db.flush()

    # Event: emit CertificationAwarded when certification is issued
    await event_bus.emit(
        Event(
            name="CertificationAwarded",
            payload={
                "certification_id": cert.id,
                "code": cert.code,
                "participant_name": cert.participant_name,
                "course_id": cert.course_id,
                "certificate_code": cert.certificate_code,
                "issued_at": str(cert.issued_at),
                "expires_at": str(cert.expires_at) if cert.expires_at else None,
            },
            source_module="training_services",
        )
    )

    return cert


@router.get("/certifications/{cert_id}", response_model=CertificationRecordResponse)
async def get_certification(cert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CertificationRecord).where(CertificationRecord.id == cert_id, CertificationRecord.is_deleted == False)
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found")
    return cert


@router.patch("/certifications/{cert_id}", response_model=CertificationRecordResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_certification(
    cert_id: int,
    payload: CertificationRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CertificationRecord).where(CertificationRecord.id == cert_id, CertificationRecord.is_deleted == False)
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cert, field, value)
    await db.flush()
    return cert


@router.delete("/certifications/{cert_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_certification(cert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CertificationRecord).where(CertificationRecord.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert or cert.is_deleted:
        raise HTTPException(status_code=404, detail="Certification record not found")
    cert.is_deleted = True
    cert.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Certification record deleted successfully", "id": cert_id}


@router.patch("/certifications/{cert_id}/restore")
async def restore_certification(cert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CertificationRecord).where(CertificationRecord.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found")
    if not cert.is_deleted:
        raise HTTPException(status_code=400, detail="Certification record is not deleted")
    cert.is_deleted = False
    cert.deleted_at = None
    await db.commit()
    return cert


# ─── User Manual (MAN-P6-001) ────────────────────────────────────────────

@router.get("/manuals", response_model=List[UserManualResponse])
async def list_manuals(
    product: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(UserManual).where(UserManual.is_deleted == False)
    if product:
        stmt = stmt.where(UserManual.product.ilike(f"%{product}%"))
    if status_filter:
        stmt = stmt.where(UserManual.status == status_filter)
    result = await db.execute(paginate(stmt.order_by(UserManual.code), page))
    return list(result.scalars().all())


@router.post("/manuals", response_model=UserManualResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_manual(payload: UserManualCreate, db: AsyncSession = Depends(get_db)):
    manual = UserManual(**payload.model_dump())
    db.add(manual)
    await db.flush()
    return manual


@router.get("/manuals/{manual_id}", response_model=UserManualResponse)
async def get_manual(manual_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserManual).where(UserManual.id == manual_id, UserManual.is_deleted == False))
    manual = result.scalar_one_or_none()
    if not manual:
        raise HTTPException(status_code=404, detail="User manual not found")
    return manual


@router.patch("/manuals/{manual_id}", response_model=UserManualResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_manual(
    manual_id: int,
    payload: UserManualUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserManual).where(UserManual.id == manual_id, UserManual.is_deleted == False))
    manual = result.scalar_one_or_none()
    if not manual:
        raise HTTPException(status_code=404, detail="User manual not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(manual, field, value)
    await db.flush()
    return manual


@router.delete("/manuals/{manual_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_manual(manual_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserManual).where(UserManual.id == manual_id))
    manual = result.scalar_one_or_none()
    if not manual or manual.is_deleted:
        raise HTTPException(status_code=404, detail="User manual not found")
    manual.is_deleted = True
    manual.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "User manual deleted successfully", "id": manual_id}


@router.patch("/manuals/{manual_id}/restore")
async def restore_manual(manual_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserManual).where(UserManual.id == manual_id))
    manual = result.scalar_one_or_none()
    if not manual:
        raise HTTPException(status_code=404, detail="User manual not found")
    if not manual.is_deleted:
        raise HTTPException(status_code=400, detail="User manual is not deleted")
    manual.is_deleted = False
    manual.deleted_at = None
    await db.commit()
    return manual


# ─── Video Tutorial (GUIA-P6-001) ────────────────────────────────────────

@router.get("/video-tutorials", response_model=List[VideoTutorialResponse])
async def list_video_tutorials(
    course_id: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(VideoTutorial).where(VideoTutorial.is_deleted == False)
    if course_id is not None:
        stmt = stmt.where(VideoTutorial.course_id == course_id)
    if status_filter:
        stmt = stmt.where(VideoTutorial.status == status_filter)
    result = await db.execute(paginate(stmt.order_by(VideoTutorial.code), page))
    return list(result.scalars().all())


@router.post("/video-tutorials", response_model=VideoTutorialResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_video_tutorial(payload: VideoTutorialCreate, db: AsyncSession = Depends(get_db)):
    tutorial = VideoTutorial(**payload.model_dump())
    db.add(tutorial)
    await db.flush()
    return tutorial


@router.get("/video-tutorials/{tutorial_id}", response_model=VideoTutorialResponse)
async def get_video_tutorial(tutorial_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VideoTutorial).where(VideoTutorial.id == tutorial_id, VideoTutorial.is_deleted == False)
    )
    tutorial = result.scalar_one_or_none()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Video tutorial not found")
    return tutorial


@router.patch("/video-tutorials/{tutorial_id}", response_model=VideoTutorialResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_video_tutorial(
    tutorial_id: int,
    payload: VideoTutorialUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VideoTutorial).where(VideoTutorial.id == tutorial_id, VideoTutorial.is_deleted == False)
    )
    tutorial = result.scalar_one_or_none()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Video tutorial not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tutorial, field, value)
    await db.flush()
    return tutorial


@router.delete("/video-tutorials/{tutorial_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_video_tutorial(tutorial_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VideoTutorial).where(VideoTutorial.id == tutorial_id))
    tutorial = result.scalar_one_or_none()
    if not tutorial or tutorial.is_deleted:
        raise HTTPException(status_code=404, detail="Video tutorial not found")
    tutorial.is_deleted = True
    tutorial.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Video tutorial deleted successfully", "id": tutorial_id}


@router.patch("/video-tutorials/{tutorial_id}/restore")
async def restore_video_tutorial(tutorial_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VideoTutorial).where(VideoTutorial.id == tutorial_id))
    tutorial = result.scalar_one_or_none()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Video tutorial not found")
    if not tutorial.is_deleted:
        raise HTTPException(status_code=400, detail="Video tutorial is not deleted")
    tutorial.is_deleted = False
    tutorial.deleted_at = None
    await db.commit()
    return tutorial


# ─── Business Logic Endpoints ────────────────────────────────────────────

@router.get("/courses/{course_id}/effectiveness", response_model=TrainingEffectivenessResponse)
async def get_training_effectiveness(course_id: int, db: AsyncSession = Depends(get_db)):
    """Calculate training effectiveness metrics (avg score, completion rate)."""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id, Course.is_deleted == False))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    return await calculate_training_effectiveness(db, course_id)


@router.get("/certifications/by-participant/{name}", response_model=List[CertificationRecordResponse])
async def list_certifications_by_participant(name: str, db: AsyncSession = Depends(get_db)):
    """Get all certification records for a specific participant."""
    return await get_certifications_by_participant(db, name)
