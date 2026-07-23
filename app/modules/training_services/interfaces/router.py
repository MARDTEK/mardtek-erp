"""P6 — Training & Human Development: FastAPI routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.pagination import PaginationParams
from app.modules.training_services.application.services import training_service
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
    return await training_service.list_needs(db, page, priority, status_filter, role)

@router.post("/needs", response_model=TrainingNeedsResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_need(payload: TrainingNeedsCreate, db: AsyncSession = Depends(get_db)):
    return await training_service.create_need(db, payload.model_dump())

@router.get("/needs/{need_id}", response_model=TrainingNeedsResponse)
async def get_need(need_id: int, db: AsyncSession = Depends(get_db)):
    need = await training_service.get_need(db, need_id)
    if not need:
        raise HTTPException(status_code=404, detail="Training needs assessment not found")
    return need

@router.patch("/needs/{need_id}", response_model=TrainingNeedsResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_need(need_id: int, payload: TrainingNeedsUpdate, db: AsyncSession = Depends(get_db)):
    need = await training_service.update_need(db, need_id, payload.model_dump(exclude_unset=True))
    if not need:
        raise HTTPException(status_code=404, detail="Training needs assessment not found")
    return need

@router.delete("/needs/{need_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_need(need_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_need(db, need_id)
    if not success:
        raise HTTPException(status_code=404, detail="Training needs assessment not found")
    return {"message": "Training needs assessment deleted successfully", "id": need_id}

@router.patch("/needs/{need_id}/restore")
async def restore_need(need_id: int, db: AsyncSession = Depends(get_db)):
    need = await training_service.restore_need(db, need_id)
    if not need:
        raise HTTPException(status_code=404, detail="Training needs assessment not found or not deleted")
    return need

# ─── Competency Matrix (MAT-P6-001) ──────────────────────────────────────

@router.get("/competency-matrices", response_model=List[CompetencyMatrixResponse])
async def list_competency_matrices(
    role: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await training_service.list_competency_matrices(db, page, role, is_active)

@router.post("/competency-matrices", response_model=CompetencyMatrixResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_competency_matrix(payload: CompetencyMatrixCreate, db: AsyncSession = Depends(get_db)):
    return await training_service.create_competency_matrix(db, payload.model_dump())

@router.get("/competency-matrices/{matrix_id}", response_model=CompetencyMatrixResponse)
async def get_competency_matrix(matrix_id: int, db: AsyncSession = Depends(get_db)):
    matrix = await training_service.get_competency_matrix(db, matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Competency matrix not found")
    return matrix

@router.patch("/competency-matrices/{matrix_id}", response_model=CompetencyMatrixResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_competency_matrix(
    matrix_id: int,
    payload: CompetencyMatrixUpdate,
    db: AsyncSession = Depends(get_db),
):
    matrix = await training_service.update_competency_matrix(db, matrix_id, payload.model_dump(exclude_unset=True))
    if not matrix:
        raise HTTPException(status_code=404, detail="Competency matrix not found")
    return matrix

@router.delete("/competency-matrices/{matrix_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_competency_matrix(matrix_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_competency_matrix(db, matrix_id)
    if not success:
        raise HTTPException(status_code=404, detail="Competency matrix not found")
    return {"message": "Competency matrix deleted successfully", "id": matrix_id}

@router.patch("/competency-matrices/{matrix_id}/restore")
async def restore_competency_matrix(matrix_id: int, db: AsyncSession = Depends(get_db)):
    matrix = await training_service.restore_competency_matrix(db, matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Competency matrix not found or not deleted")
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
    matrix = await training_service.update_competency_gap(db, matrix_id, payload.role, payload.competencies)
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
    return await training_service.list_courses(db, page, modality, status_filter)

@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_course(payload: CourseCreate, db: AsyncSession = Depends(get_db)):
    return await training_service.create_course(db, payload.model_dump())

@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    course = await training_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.patch("/courses/{course_id}", response_model=CourseResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_course(course_id: int, payload: CourseUpdate, db: AsyncSession = Depends(get_db)):
    course = await training_service.update_course(db, course_id, payload.model_dump(exclude_unset=True))
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.delete("/courses/{course_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_course(db, course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted successfully", "id": course_id}

@router.patch("/courses/{course_id}/restore")
async def restore_course(course_id: int, db: AsyncSession = Depends(get_db)):
    course = await training_service.restore_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not deleted")
    return course

# ─── Training Plan (PLN-P6-001) ──────────────────────────────────────────

@router.get("/plans", response_model=List[TrainingPlanResponse])
async def list_plans(
    year: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await training_service.list_plans(db, page, year, status_filter)

@router.post("/plans", response_model=TrainingPlanResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_plan(payload: TrainingPlanCreate, db: AsyncSession = Depends(get_db)):
    return await training_service.create_plan(db, payload.model_dump())

@router.get("/plans/{plan_id}", response_model=TrainingPlanResponse)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    plan = await training_service.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    return plan

@router.patch("/plans/{plan_id}", response_model=TrainingPlanResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_plan(plan_id: int, payload: TrainingPlanUpdate, db: AsyncSession = Depends(get_db)):
    plan = await training_service.update_plan(db, plan_id, payload.model_dump(exclude_unset=True))
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    return plan

@router.delete("/plans/{plan_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_plan(db, plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Training plan not found")
    return {"message": "Training plan deleted successfully", "id": plan_id}

@router.patch("/plans/{plan_id}/restore")
async def restore_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    plan = await training_service.restore_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found or not deleted")
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
    return await training_service.list_sessions(db, page, course_id, status_filter, instructor)

@router.post("/sessions", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_session(payload: TrainingSessionCreate, db: AsyncSession = Depends(get_db)):
    session = await training_service.create_session(db, payload.model_dump())
    if not session:
        raise HTTPException(status_code=404, detail="Course not found")
    return session

@router.get("/sessions/{session_id}", response_model=TrainingSessionResponse)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await training_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Training session not found")
    return session

@router.patch("/sessions/{session_id}", response_model=TrainingSessionResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_session(
    session_id: int,
    payload: TrainingSessionUpdate,
    db: AsyncSession = Depends(get_db),
):
    session = await training_service.update_session(db, session_id, payload.model_dump(exclude_unset=True))
    if not session:
        raise HTTPException(status_code=404, detail="Training session not found")
    return session

@router.delete("/sessions/{session_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Training session not found")
    return {"message": "Training session deleted successfully", "id": session_id}

@router.patch("/sessions/{session_id}/restore")
async def restore_session(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await training_service.restore_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Training session not found or not deleted")
    return session

# ─── Training Evaluation (FO-P6-002) ─────────────────────────────────────

@router.get("/evaluations", response_model=List[TrainingEvaluationResponse])
async def list_evaluations(
    session_id: int | None = None,
    participant: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await training_service.list_evaluations(db, page, session_id, participant)

@router.post("/evaluations", response_model=TrainingEvaluationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_evaluation(payload: TrainingEvaluationCreate, db: AsyncSession = Depends(get_db)):
    evaluation = await training_service.create_evaluation(db, payload.model_dump())
    if not evaluation:
        raise HTTPException(status_code=404, detail="Training session not found")
    return evaluation

@router.patch("/evaluations/{evaluation_id}", response_model=TrainingEvaluationResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_evaluation(
    evaluation_id: int,
    payload: TrainingEvaluationUpdate,
    db: AsyncSession = Depends(get_db),
):
    evaluation = await training_service.update_evaluation(db, evaluation_id, payload.model_dump(exclude_unset=True))
    if not evaluation:
        raise HTTPException(status_code=404, detail="Training evaluation not found")
    return evaluation

@router.delete("/evaluations/{evaluation_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_evaluation(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_evaluation(db, evaluation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Training evaluation not found")
    return {"message": "Training evaluation deleted successfully", "id": evaluation_id}

@router.patch("/evaluations/{evaluation_id}/restore")
async def restore_evaluation(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    evaluation = await training_service.restore_evaluation(db, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Training evaluation not found or not deleted")
    return evaluation

@router.get("/courses/{course_id}/effectiveness", response_model=TrainingEffectivenessResponse)
async def get_training_effectiveness(course_id: int, db: AsyncSession = Depends(get_db)):
    course = await training_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return await training_service.calculate_training_effectiveness(db, course_id)

# ─── Attendance Record (REG-P6-001) ──────────────────────────────────────

@router.get("/attendance", response_model=List[AttendanceRecordResponse])
async def list_attendance(
    session_id: int | None = None,
    participant_name: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await training_service.list_attendance(db, page, session_id, participant_name)

@router.post("/attendance", response_model=AttendanceRecordResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_attendance(payload: AttendanceRecordCreate, db: AsyncSession = Depends(get_db)):
    record = await training_service.create_attendance(db, payload.model_dump())
    if not record:
        raise HTTPException(status_code=404, detail="Training session not found")
    return record

@router.get("/attendance/{record_id}", response_model=AttendanceRecordResponse)
async def get_attendance(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await training_service.get_attendance(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record

@router.patch("/attendance/{record_id}", response_model=AttendanceRecordResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_attendance(
    record_id: int,
    payload: AttendanceRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    record = await training_service.update_attendance(db, record_id, payload.model_dump(exclude_unset=True))
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record

@router.delete("/attendance/{record_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_attendance(record_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_attendance(db, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return {"message": "Attendance record deleted successfully", "id": record_id}

@router.patch("/attendance/{record_id}/restore")
async def restore_attendance(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await training_service.restore_attendance(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found or not deleted")
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
    return await training_service.list_certifications(db, page, participant_name, status_filter, course_id)

@router.post(
    "/certifications",
    response_model=CertificationRecordResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_certification(payload: CertificationRecordCreate, db: AsyncSession = Depends(get_db)):
    cert = await training_service.create_certification(db, payload.model_dump())
    if not cert:
        raise HTTPException(status_code=404, detail="Course not found")
    return cert

@router.get("/certifications/{cert_id}", response_model=CertificationRecordResponse)
async def get_certification(cert_id: int, db: AsyncSession = Depends(get_db)):
    cert = await training_service.get_certification(db, cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found")
    return cert

@router.patch("/certifications/{cert_id}", response_model=CertificationRecordResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_certification(
    cert_id: int,
    payload: CertificationRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    cert = await training_service.update_certification(db, cert_id, payload.model_dump(exclude_unset=True))
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found")
    return cert

@router.delete("/certifications/{cert_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_certification(cert_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_certification(db, cert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Certification record not found")
    return {"message": "Certification record deleted successfully", "id": cert_id}

@router.patch("/certifications/{cert_id}/restore")
async def restore_certification(cert_id: int, db: AsyncSession = Depends(get_db)):
    cert = await training_service.restore_certification(db, cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found or not deleted")
    return cert

# ─── User Manual (MAN-P6-001) ────────────────────────────────────────────

@router.get("/manuals", response_model=List[UserManualResponse])
async def list_manuals(
    product: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await training_service.list_manuals(db, page, product, status_filter)

@router.post("/manuals", response_model=UserManualResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_manual(payload: UserManualCreate, db: AsyncSession = Depends(get_db)):
    return await training_service.create_manual(db, payload.model_dump())

@router.get("/manuals/{manual_id}", response_model=UserManualResponse)
async def get_manual(manual_id: int, db: AsyncSession = Depends(get_db)):
    manual = await training_service.get_manual(db, manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="User manual not found")
    return manual

@router.patch("/manuals/{manual_id}", response_model=UserManualResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_manual(
    manual_id: int,
    payload: UserManualUpdate,
    db: AsyncSession = Depends(get_db),
):
    manual = await training_service.update_manual(db, manual_id, payload.model_dump(exclude_unset=True))
    if not manual:
        raise HTTPException(status_code=404, detail="User manual not found")
    return manual

@router.delete("/manuals/{manual_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_manual(manual_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_manual(db, manual_id)
    if not success:
        raise HTTPException(status_code=404, detail="User manual not found")
    return {"message": "User manual deleted successfully", "id": manual_id}

@router.patch("/manuals/{manual_id}/restore")
async def restore_manual(manual_id: int, db: AsyncSession = Depends(get_db)):
    manual = await training_service.restore_manual(db, manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="User manual not found or not deleted")
    return manual

# ─── Video Tutorial (VID-P6-001) ─────────────────────────────────────────

@router.get("/video-tutorials", response_model=List[VideoTutorialResponse])
async def list_videos(
    module: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    return await training_service.list_videos(db, page, module)

@router.post("/video-tutorials", response_model=VideoTutorialResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_video(payload: VideoTutorialCreate, db: AsyncSession = Depends(get_db)):
    return await training_service.create_video(db, payload.model_dump())

@router.get("/video-tutorials/{video_id}", response_model=VideoTutorialResponse)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await training_service.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video tutorial not found")
    return video

@router.patch("/video-tutorials/{video_id}", response_model=VideoTutorialResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_video(
    video_id: int,
    payload: VideoTutorialUpdate,
    db: AsyncSession = Depends(get_db),
):
    video = await training_service.update_video(db, video_id, payload.model_dump(exclude_unset=True))
    if not video:
        raise HTTPException(status_code=404, detail="Video tutorial not found")
    return video

@router.delete("/video-tutorials/{video_id}", dependencies=[Depends(RoleChecker("admin", "manager"))])
async def delete_video(video_id: int, db: AsyncSession = Depends(get_db)):
    success = await training_service.delete_video(db, video_id)
    if not success:
        raise HTTPException(status_code=404, detail="Video tutorial not found")
    return {"message": "Video tutorial deleted successfully", "id": video_id}

@router.patch("/video-tutorials/{video_id}/restore")
async def restore_video(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await training_service.restore_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video tutorial not found or not deleted")
    return video
