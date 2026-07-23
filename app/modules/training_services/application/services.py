"""Application services for P6 — Training & Human Development."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import Event, event_bus
from app.core.pagination import PaginationParams, paginate
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
from app.modules.training_services.infrastructure.repositories import (
    attendance_record_repo,
    certification_record_repo,
    competency_matrix_repo,
    course_repo,
    training_evaluation_repo,
    training_needs_repo,
    training_plan_repo,
    training_session_repo,
    user_manual_repo,
    video_tutorial_repo,
)

class TrainingService:
    # ─── Training Needs Assessment ───────────────────────────────────────────
    @staticmethod
    async def list_needs(db: AsyncSession, page: PaginationParams, priority: str | None = None, status_filter: str | None = None, role: str | None = None) -> List[TrainingNeedsAssessment]:
        stmt = select(TrainingNeedsAssessment).where(TrainingNeedsAssessment.is_deleted == False)
        if priority:
            stmt = stmt.where(TrainingNeedsAssessment.priority == priority)
        if status_filter:
            stmt = stmt.where(TrainingNeedsAssessment.status == status_filter)
        if role:
            stmt = stmt.where(TrainingNeedsAssessment.role.ilike(f"%{role}%"))
        result = await db.execute(paginate(stmt.order_by(TrainingNeedsAssessment.code), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_need(db: AsyncSession, data: dict) -> TrainingNeedsAssessment:
        need = TrainingNeedsAssessment(**data)
        training_needs_repo.add(db, need)
        await db.flush()
        return need

    @staticmethod
    async def get_need(db: AsyncSession, need_id: int) -> Optional[TrainingNeedsAssessment]:
        result = await db.execute(select(TrainingNeedsAssessment).where(TrainingNeedsAssessment.id == need_id, TrainingNeedsAssessment.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_need(db: AsyncSession, need_id: int, data: dict) -> Optional[TrainingNeedsAssessment]:
        need = await TrainingService.get_need(db, need_id)
        if not need: return None
        for k, v in data.items(): setattr(need, k, v)
        await db.flush()
        return need

    @staticmethod
    async def delete_need(db: AsyncSession, need_id: int) -> bool:
        need = await TrainingService.get_need(db, need_id)
        if not need: return False
        await training_needs_repo.delete(db, need)
        await db.flush()
        return True

    @staticmethod
    async def restore_need(db: AsyncSession, need_id: int) -> Optional[TrainingNeedsAssessment]:
        result = await db.execute(select(TrainingNeedsAssessment).where(TrainingNeedsAssessment.id == need_id))
        need = result.scalar_one_or_none()
        if not need or not need.is_deleted: return None
        need.is_deleted = False
        need.deleted_at = None
        await db.flush()
        return need

    # ─── Competency Matrix ───────────────────────────────────────────────────
    @staticmethod
    async def list_competency_matrices(db: AsyncSession, page: PaginationParams, role: str | None = None, is_active: bool | None = None) -> List[CompetencyMatrix]:
        stmt = select(CompetencyMatrix).where(CompetencyMatrix.is_deleted == False)
        if role:
            stmt = stmt.where(CompetencyMatrix.role.ilike(f"%{role}%"))
        if is_active is not None:
            stmt = stmt.where(CompetencyMatrix.is_active == is_active)
        result = await db.execute(paginate(stmt.order_by(CompetencyMatrix.code), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_competency_matrix(db: AsyncSession, data: dict) -> CompetencyMatrix:
        matrix = CompetencyMatrix(**data)
        competency_matrix_repo.add(db, matrix)
        await db.flush()
        return matrix

    @staticmethod
    async def get_competency_matrix(db: AsyncSession, matrix_id: int) -> Optional[CompetencyMatrix]:
        result = await db.execute(select(CompetencyMatrix).where(CompetencyMatrix.id == matrix_id, CompetencyMatrix.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_competency_matrix(db: AsyncSession, matrix_id: int, data: dict) -> Optional[CompetencyMatrix]:
        matrix = await TrainingService.get_competency_matrix(db, matrix_id)
        if not matrix: return None
        for k, v in data.items(): setattr(matrix, k, v)
        await db.flush()
        return matrix

    @staticmethod
    async def delete_competency_matrix(db: AsyncSession, matrix_id: int) -> bool:
        matrix = await TrainingService.get_competency_matrix(db, matrix_id)
        if not matrix: return False
        await competency_matrix_repo.delete(db, matrix)
        await db.flush()
        return True

    @staticmethod
    async def restore_competency_matrix(db: AsyncSession, matrix_id: int) -> Optional[CompetencyMatrix]:
        result = await db.execute(select(CompetencyMatrix).where(CompetencyMatrix.id == matrix_id))
        matrix = result.scalar_one_or_none()
        if not matrix or not matrix.is_deleted: return None
        matrix.is_deleted = False
        matrix.deleted_at = None
        await db.flush()
        return matrix

    @staticmethod
    async def update_competency_gap(db: AsyncSession, matrix_id: int, role: str, competencies: list) -> Optional[CompetencyMatrix]:
        matrix = await TrainingService.get_competency_matrix(db, matrix_id)
        if not matrix: return None
        matrix.role = role
        matrix.competencies = competencies
        
        # Recalculate gap
        gap_count = 0
        for comp in competencies:
            req = comp.get("required_level", 0)
            curr = comp.get("current_level", 0)
            if curr < req:
                gap_count += (req - curr)
                
        matrix.gap_score = gap_count
        await db.flush()
        return matrix

    # ─── Course ──────────────────────────────────────────────────────────────
    @staticmethod
    async def list_courses(db: AsyncSession, page: PaginationParams, modality: str | None = None, status_filter: str | None = None) -> List[Course]:
        stmt = select(Course).where(Course.is_deleted == False)
        if modality: stmt = stmt.where(Course.modality == modality)
        if status_filter: stmt = stmt.where(Course.status == status_filter)
        result = await db.execute(paginate(stmt.order_by(Course.code), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_course(db: AsyncSession, data: dict) -> Course:
        course = Course(**data)
        course_repo.add(db, course)
        await db.flush()
        return course

    @staticmethod
    async def get_course(db: AsyncSession, course_id: int) -> Optional[Course]:
        result = await db.execute(select(Course).where(Course.id == course_id, Course.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_course(db: AsyncSession, course_id: int, data: dict) -> Optional[Course]:
        course = await TrainingService.get_course(db, course_id)
        if not course: return None
        for k, v in data.items(): setattr(course, k, v)
        await db.flush()
        return course

    @staticmethod
    async def delete_course(db: AsyncSession, course_id: int) -> bool:
        course = await TrainingService.get_course(db, course_id)
        if not course: return False
        await course_repo.delete(db, course)
        await db.flush()
        return True

    @staticmethod
    async def restore_course(db: AsyncSession, course_id: int) -> Optional[Course]:
        result = await db.execute(select(Course).where(Course.id == course_id))
        course = result.scalar_one_or_none()
        if not course or not course.is_deleted: return None
        course.is_deleted = False
        course.deleted_at = None
        await db.flush()
        return course

    # ─── Training Plan ───────────────────────────────────────────────────────
    @staticmethod
    async def list_plans(db: AsyncSession, page: PaginationParams, year: int | None = None, status_filter: str | None = None) -> List[TrainingPlan]:
        stmt = select(TrainingPlan).where(TrainingPlan.is_deleted == False)
        if year: stmt = stmt.where(TrainingPlan.year == year)
        if status_filter: stmt = stmt.where(TrainingPlan.status == status_filter)
        result = await db.execute(paginate(stmt.order_by(TrainingPlan.year.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_plan(db: AsyncSession, data: dict) -> TrainingPlan:
        plan = TrainingPlan(**data)
        training_plan_repo.add(db, plan)
        await db.flush()
        return plan

    @staticmethod
    async def get_plan(db: AsyncSession, plan_id: int) -> Optional[TrainingPlan]:
        result = await db.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id, TrainingPlan.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_plan(db: AsyncSession, plan_id: int, data: dict) -> Optional[TrainingPlan]:
        plan = await TrainingService.get_plan(db, plan_id)
        if not plan: return None
        for k, v in data.items(): setattr(plan, k, v)
        await db.flush()
        return plan

    @staticmethod
    async def delete_plan(db: AsyncSession, plan_id: int) -> bool:
        plan = await TrainingService.get_plan(db, plan_id)
        if not plan: return False
        await training_plan_repo.delete(db, plan)
        await db.flush()
        return True

    @staticmethod
    async def restore_plan(db: AsyncSession, plan_id: int) -> Optional[TrainingPlan]:
        result = await db.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan or not plan.is_deleted: return None
        plan.is_deleted = False
        plan.deleted_at = None
        await db.flush()
        return plan

    # ─── Training Session ────────────────────────────────────────────────────
    @staticmethod
    async def list_sessions(db: AsyncSession, page: PaginationParams, course_id: int | None = None, status_filter: str | None = None, instructor: str | None = None) -> List[TrainingSession]:
        stmt = select(TrainingSession).where(TrainingSession.is_deleted == False)
        if course_id is not None: stmt = stmt.where(TrainingSession.course_id == course_id)
        if status_filter: stmt = stmt.where(TrainingSession.status == status_filter)
        if instructor: stmt = stmt.where(TrainingSession.instructor.ilike(f"%{instructor}%"))
        result = await db.execute(paginate(stmt.order_by(TrainingSession.start_date.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_session(db: AsyncSession, data: dict) -> Optional[TrainingSession]:
        course = await TrainingService.get_course(db, data.get("course_id"))
        if not course: return None
        session = TrainingSession(**data)
        training_session_repo.add(db, session)
        await db.flush()
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: int) -> Optional[TrainingSession]:
        result = await db.execute(select(TrainingSession).where(TrainingSession.id == session_id, TrainingSession.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_session(db: AsyncSession, session_id: int, data: dict) -> Optional[TrainingSession]:
        session = await TrainingService.get_session(db, session_id)
        if not session: return None
        old_status = session.status
        for k, v in data.items(): setattr(session, k, v)
        await db.flush()

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

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: int) -> bool:
        session = await TrainingService.get_session(db, session_id)
        if not session: return False
        await training_session_repo.delete(db, session)
        await db.flush()
        return True

    @staticmethod
    async def restore_session(db: AsyncSession, session_id: int) -> Optional[TrainingSession]:
        result = await db.execute(select(TrainingSession).where(TrainingSession.id == session_id))
        session = result.scalar_one_or_none()
        if not session or not session.is_deleted: return None
        session.is_deleted = False
        session.deleted_at = None
        await db.flush()
        return session

    # ─── Training Evaluation ─────────────────────────────────────────────────
    @staticmethod
    async def list_evaluations(db: AsyncSession, page: PaginationParams, session_id: int | None = None, participant: str | None = None) -> List[TrainingEvaluation]:
        stmt = select(TrainingEvaluation).where(TrainingEvaluation.is_deleted == False)
        if session_id is not None: stmt = stmt.where(TrainingEvaluation.session_id == session_id)
        if participant: stmt = stmt.where(TrainingEvaluation.participant.ilike(f"%{participant}%"))
        result = await db.execute(paginate(stmt.order_by(TrainingEvaluation.submitted_at.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_evaluation(db: AsyncSession, data: dict) -> Optional[TrainingEvaluation]:
        session = await TrainingService.get_session(db, data.get("session_id"))
        if not session: return None
        evaluation = TrainingEvaluation(**data)
        training_evaluation_repo.add(db, evaluation)
        await db.flush()
        return evaluation

    @staticmethod
    async def get_evaluation(db: AsyncSession, evaluation_id: int) -> Optional[TrainingEvaluation]:
        result = await db.execute(select(TrainingEvaluation).where(TrainingEvaluation.id == evaluation_id, TrainingEvaluation.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_evaluation(db: AsyncSession, evaluation_id: int, data: dict) -> Optional[TrainingEvaluation]:
        evaluation = await TrainingService.get_evaluation(db, evaluation_id)
        if not evaluation: return None
        for k, v in data.items(): setattr(evaluation, k, v)
        await db.flush()
        return evaluation

    @staticmethod
    async def delete_evaluation(db: AsyncSession, evaluation_id: int) -> bool:
        evaluation = await TrainingService.get_evaluation(db, evaluation_id)
        if not evaluation: return False
        await training_evaluation_repo.delete(db, evaluation)
        await db.flush()
        return True

    @staticmethod
    async def restore_evaluation(db: AsyncSession, evaluation_id: int) -> Optional[TrainingEvaluation]:
        result = await db.execute(select(TrainingEvaluation).where(TrainingEvaluation.id == evaluation_id))
        evaluation = result.scalar_one_or_none()
        if not evaluation or not evaluation.is_deleted: return None
        evaluation.is_deleted = False
        evaluation.deleted_at = None
        await db.flush()
        return evaluation

    @staticmethod
    async def calculate_training_effectiveness(db: AsyncSession, course_id: int) -> Dict[str, Any]:
        sessions = await training_session_repo.get_by_course(db, course_id)
        if not sessions:
            return {"course_id": course_id, "total_sessions": 0, "total_participants": 0, "average_score": 0.0, "completion_rate": 0.0}

        session_ids = [s.id for s in sessions]
        avg_score = await training_evaluation_repo.get_avg_score_by_sessions(db, session_ids)
        total_participants = sum(len(s.attendees) for s in sessions if s.attendees)
        
        completed_sessions = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)
        completion_rate = (completed_sessions / len(sessions)) * 100

        return {
            "course_id": course_id,
            "total_sessions": len(sessions),
            "total_participants": total_participants,
            "average_score": round(avg_score, 2),
            "completion_rate": round(completion_rate, 2),
        }

    # ─── Attendance Record ───────────────────────────────────────────────────
    @staticmethod
    async def list_attendance(db: AsyncSession, page: PaginationParams, session_id: int | None = None, participant_name: str | None = None) -> List[AttendanceRecord]:
        stmt = select(AttendanceRecord).where(AttendanceRecord.is_deleted == False)
        if session_id is not None: stmt = stmt.where(AttendanceRecord.session_id == session_id)
        if participant_name: stmt = stmt.where(AttendanceRecord.participant_name.ilike(f"%{participant_name}%"))
        result = await db.execute(paginate(stmt.order_by(AttendanceRecord.signed_at.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_attendance(db: AsyncSession, data: dict) -> Optional[AttendanceRecord]:
        session = await TrainingService.get_session(db, data.get("session_id"))
        if not session: return None
        record = AttendanceRecord(**data)
        attendance_record_repo.add(db, record)
        await db.flush()
        return record

    @staticmethod
    async def get_attendance(db: AsyncSession, record_id: int) -> Optional[AttendanceRecord]:
        result = await db.execute(select(AttendanceRecord).where(AttendanceRecord.id == record_id, AttendanceRecord.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_attendance(db: AsyncSession, record_id: int, data: dict) -> Optional[AttendanceRecord]:
        record = await TrainingService.get_attendance(db, record_id)
        if not record: return None
        for k, v in data.items(): setattr(record, k, v)
        await db.flush()
        return record

    @staticmethod
    async def delete_attendance(db: AsyncSession, record_id: int) -> bool:
        record = await TrainingService.get_attendance(db, record_id)
        if not record: return False
        await attendance_record_repo.delete(db, record)
        await db.flush()
        return True

    @staticmethod
    async def restore_attendance(db: AsyncSession, record_id: int) -> Optional[AttendanceRecord]:
        result = await db.execute(select(AttendanceRecord).where(AttendanceRecord.id == record_id))
        record = result.scalar_one_or_none()
        if not record or not record.is_deleted: return None
        record.is_deleted = False
        record.deleted_at = None
        await db.flush()
        return record

    # ─── Certification Record ────────────────────────────────────────────────
    @staticmethod
    async def list_certifications(db: AsyncSession, page: PaginationParams, participant_name: str | None = None, status_filter: str | None = None, course_id: int | None = None) -> List[CertificationRecord]:
        stmt = select(CertificationRecord).where(CertificationRecord.is_deleted == False)
        if participant_name: stmt = stmt.where(CertificationRecord.participant_name.ilike(f"%{participant_name}%"))
        if status_filter: stmt = stmt.where(CertificationRecord.status == status_filter)
        if course_id is not None: stmt = stmt.where(CertificationRecord.course_id == course_id)
        result = await db.execute(paginate(stmt.order_by(CertificationRecord.issued_at.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_certification(db: AsyncSession, data: dict) -> Optional[CertificationRecord]:
        course = await TrainingService.get_course(db, data.get("course_id"))
        if not course: return None
        cert = CertificationRecord(**data)
        certification_record_repo.add(db, cert)
        await db.flush()
        
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

    @staticmethod
    async def get_certification(db: AsyncSession, cert_id: int) -> Optional[CertificationRecord]:
        result = await db.execute(select(CertificationRecord).where(CertificationRecord.id == cert_id, CertificationRecord.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_certification(db: AsyncSession, cert_id: int, data: dict) -> Optional[CertificationRecord]:
        cert = await TrainingService.get_certification(db, cert_id)
        if not cert: return None
        for k, v in data.items(): setattr(cert, k, v)
        await db.flush()
        return cert

    @staticmethod
    async def delete_certification(db: AsyncSession, cert_id: int) -> bool:
        cert = await TrainingService.get_certification(db, cert_id)
        if not cert: return False
        await certification_record_repo.delete(db, cert)
        await db.flush()
        return True

    @staticmethod
    async def restore_certification(db: AsyncSession, cert_id: int) -> Optional[CertificationRecord]:
        result = await db.execute(select(CertificationRecord).where(CertificationRecord.id == cert_id))
        cert = result.scalar_one_or_none()
        if not cert or not cert.is_deleted: return None
        cert.is_deleted = False
        cert.deleted_at = None
        await db.flush()
        return cert

    # ─── User Manual ─────────────────────────────────────────────────────────
    @staticmethod
    async def list_manuals(db: AsyncSession, page: PaginationParams, product: str | None = None, status_filter: str | None = None) -> List[UserManual]:
        stmt = select(UserManual).where(UserManual.is_deleted == False)
        if product: stmt = stmt.where(UserManual.product.ilike(f"%{product}%"))
        if status_filter: stmt = stmt.where(UserManual.status == status_filter)
        result = await db.execute(paginate(stmt.order_by(UserManual.version.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_manual(db: AsyncSession, data: dict) -> UserManual:
        manual = UserManual(**data)
        user_manual_repo.add(db, manual)
        await db.flush()
        return manual

    @staticmethod
    async def get_manual(db: AsyncSession, manual_id: int) -> Optional[UserManual]:
        result = await db.execute(select(UserManual).where(UserManual.id == manual_id, UserManual.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_manual(db: AsyncSession, manual_id: int, data: dict) -> Optional[UserManual]:
        manual = await TrainingService.get_manual(db, manual_id)
        if not manual: return None
        for k, v in data.items(): setattr(manual, k, v)
        await db.flush()
        return manual

    @staticmethod
    async def delete_manual(db: AsyncSession, manual_id: int) -> bool:
        manual = await TrainingService.get_manual(db, manual_id)
        if not manual: return False
        await user_manual_repo.delete(db, manual)
        await db.flush()
        return True

    @staticmethod
    async def restore_manual(db: AsyncSession, manual_id: int) -> Optional[UserManual]:
        result = await db.execute(select(UserManual).where(UserManual.id == manual_id))
        manual = result.scalar_one_or_none()
        if not manual or not manual.is_deleted: return None
        manual.is_deleted = False
        manual.deleted_at = None
        await db.flush()
        return manual

    # ─── Video Tutorial ──────────────────────────────────────────────────────
    @staticmethod
    async def list_videos(db: AsyncSession, page: PaginationParams, module: str | None = None) -> List[VideoTutorial]:
        stmt = select(VideoTutorial).where(VideoTutorial.is_deleted == False)
        if module: stmt = stmt.where(VideoTutorial.target_module == module)
        result = await db.execute(paginate(stmt.order_by(VideoTutorial.id.desc()), page))
        return list(result.scalars().all())

    @staticmethod
    async def create_video(db: AsyncSession, data: dict) -> VideoTutorial:
        video = VideoTutorial(**data)
        video_tutorial_repo.add(db, video)
        await db.flush()
        return video

    @staticmethod
    async def get_video(db: AsyncSession, video_id: int) -> Optional[VideoTutorial]:
        result = await db.execute(select(VideoTutorial).where(VideoTutorial.id == video_id, VideoTutorial.is_deleted == False))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_video(db: AsyncSession, video_id: int, data: dict) -> Optional[VideoTutorial]:
        video = await TrainingService.get_video(db, video_id)
        if not video: return None
        for k, v in data.items(): setattr(video, k, v)
        await db.flush()
        return video

    @staticmethod
    async def delete_video(db: AsyncSession, video_id: int) -> bool:
        video = await TrainingService.get_video(db, video_id)
        if not video: return False
        await video_tutorial_repo.delete(db, video)
        await db.flush()
        return True

    @staticmethod
    async def restore_video(db: AsyncSession, video_id: int) -> Optional[VideoTutorial]:
        result = await db.execute(select(VideoTutorial).where(VideoTutorial.id == video_id))
        video = result.scalar_one_or_none()
        if not video or not video.is_deleted: return None
        video.is_deleted = False
        video.deleted_at = None
        await db.flush()
        return video

training_service = TrainingService()
