from typing import Optional, TypeVar, Generic, Type
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[T]:
        result = await db.execute(select(self.model_class).where(self.model_class.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        filters: Optional[dict] = None,
        order_by=None,
        include_deleted: bool = False,
    ) -> list[T]:
        stmt = select(self.model_class)
        if not include_deleted and hasattr(self.model_class, "is_deleted"):
            stmt = stmt.where(self.model_class.is_deleted == False)
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    stmt = stmt.where(getattr(self.model_class, field_name) == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    def add(self, db: AsyncSession, obj: T) -> None:
        db.add(obj)

    async def delete(self, db: AsyncSession, obj: T) -> None:
        if hasattr(obj, "is_deleted"):
            obj.is_deleted = True
            obj.deleted_at = datetime.now(timezone.utc)
        else:
            await db.delete(obj)


class TrainingNeedsAssessmentRepository(BaseRepository[TrainingNeedsAssessment]):
    def __init__(self):
        super().__init__(TrainingNeedsAssessment)


class CompetencyMatrixRepository(BaseRepository[CompetencyMatrix]):
    def __init__(self):
        super().__init__(CompetencyMatrix)


class CourseRepository(BaseRepository[Course]):
    def __init__(self):
        super().__init__(Course)


class TrainingPlanRepository(BaseRepository[TrainingPlan]):
    def __init__(self):
        super().__init__(TrainingPlan)


class TrainingSessionRepository(BaseRepository[TrainingSession]):
    def __init__(self):
        super().__init__(TrainingSession)

    async def get_by_course(self, db: AsyncSession, course_id: int) -> list[TrainingSession]:
        result = await db.execute(
            select(TrainingSession).where(TrainingSession.course_id == course_id)
        )
        return list(result.scalars().all())


class TrainingEvaluationRepository(BaseRepository[TrainingEvaluation]):
    def __init__(self):
        super().__init__(TrainingEvaluation)

    async def get_avg_score_by_sessions(self, db: AsyncSession, session_ids: list[int]) -> float:
        if not session_ids:
            return 0.0
        result = await db.execute(
            select(func.avg(TrainingEvaluation.score)).where(
                TrainingEvaluation.session_id.in_(session_ids)
            )
        )
        return float(result.scalar() or 0.0)


class AttendanceRecordRepository(BaseRepository[AttendanceRecord]):
    def __init__(self):
        super().__init__(AttendanceRecord)


class CertificationRecordRepository(BaseRepository[CertificationRecord]):
    def __init__(self):
        super().__init__(CertificationRecord)

    async def get_by_participant(self, db: AsyncSession, name: str) -> list[CertificationRecord]:
        result = await db.execute(
            select(CertificationRecord)
            .where(CertificationRecord.participant_name == name)
            .order_by(CertificationRecord.issued_at.desc())
        )
        return list(result.scalars().all())


class UserManualRepository(BaseRepository[UserManual]):
    def __init__(self):
        super().__init__(UserManual)


class VideoTutorialRepository(BaseRepository[VideoTutorial]):
    def __init__(self):
        super().__init__(VideoTutorial)


# Singletons
training_needs_repo = TrainingNeedsAssessmentRepository()
competency_matrix_repo = CompetencyMatrixRepository()
course_repo = CourseRepository()
training_plan_repo = TrainingPlanRepository()
training_session_repo = TrainingSessionRepository()
training_evaluation_repo = TrainingEvaluationRepository()
attendance_record_repo = AttendanceRecordRepository()
certification_record_repo = CertificationRecordRepository()
user_manual_repo = UserManualRepository()
video_tutorial_repo = VideoTutorialRepository()
