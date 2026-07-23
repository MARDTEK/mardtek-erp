from typing import Optional, TypeVar, Generic, Type
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pmo_projects.domain.models import (
    ChangeRequest,
    CRStatus,
    DeliverablesChecklist,
    FollowUpMeeting,
    HandoverAcceptance,
    Project,
    ProjectClosureRecord,
    ProjectExecutionPlan,
    WeeklyProgressReport,
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
    ) -> list[T]:
        stmt = select(self.model_class)
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
        await db.delete(obj)


class ProjectRepository(BaseRepository[Project]):
    def __init__(self):
        super().__init__(Project)


class ExecutionPlanRepository(BaseRepository[ProjectExecutionPlan]):
    def __init__(self):
        super().__init__(ProjectExecutionPlan)

    async def get_by_project(self, db: AsyncSession, project_id: int) -> Optional["ProjectExecutionPlan"]:
        result = await db.execute(
            select(ProjectExecutionPlan).where(ProjectExecutionPlan.project_id == project_id)
        )
        return result.scalar_one_or_none()


class ChangeRequestRepository(BaseRepository[ChangeRequest]):
    def __init__(self):
        super().__init__(ChangeRequest)

    async def get_open_by_project(self, db: AsyncSession, project_id: int) -> list["ChangeRequest"]:
        result = await db.execute(
            select(ChangeRequest).where(
                ChangeRequest.project_id == project_id,
                ChangeRequest.status == CRStatus.SUBMITTED,
            ).order_by(ChangeRequest.created_at.asc())
        )
        return list(result.scalars().all())


class WeeklyReportRepository(BaseRepository[WeeklyProgressReport]):
    def __init__(self):
        super().__init__(WeeklyProgressReport)


class DeliverablesChecklistRepository(BaseRepository[DeliverablesChecklist]):
    def __init__(self):
        super().__init__(DeliverablesChecklist)

    async def get_by_project(self, db: AsyncSession, project_id: int) -> Optional["DeliverablesChecklist"]:
        result = await db.execute(
            select(DeliverablesChecklist).where(DeliverablesChecklist.project_id == project_id)
        )
        return result.scalar_one_or_none()


class FollowUpMeetingRepository(BaseRepository[FollowUpMeeting]):
    def __init__(self):
        super().__init__(FollowUpMeeting)


class HandoverAcceptanceRepository(BaseRepository[HandoverAcceptance]):
    def __init__(self):
        super().__init__(HandoverAcceptance)

    async def get_by_project(self, db: AsyncSession, project_id: int) -> Optional["HandoverAcceptance"]:
        result = await db.execute(
            select(HandoverAcceptance).where(HandoverAcceptance.project_id == project_id)
        )
        return result.scalar_one_or_none()


class ClosureRecordRepository(BaseRepository[ProjectClosureRecord]):
    def __init__(self):
        super().__init__(ProjectClosureRecord)

    async def get_by_project(self, db: AsyncSession, project_id: int) -> Optional["ProjectClosureRecord"]:
        result = await db.execute(
            select(ProjectClosureRecord).where(ProjectClosureRecord.project_id == project_id)
        )
        return result.scalar_one_or_none()


# Singletons
project_repo = ProjectRepository()
execution_plan_repo = ExecutionPlanRepository()
change_request_repo = ChangeRequestRepository()
weekly_report_repo = WeeklyReportRepository()
deliverables_checklist_repo = DeliverablesChecklistRepository()
follow_up_meeting_repo = FollowUpMeetingRepository()
handover_acceptance_repo = HandoverAcceptanceRepository()
closure_record_repo = ClosureRecordRepository()
