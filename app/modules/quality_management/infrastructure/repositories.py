from typing import Optional, TypeVar, Generic, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quality_management.domain.models import (
    AuditChecklistItem,
    ContinuousImprovement,
    CorrectiveAction,
    Document,
    InternalAudit,
    NonConformity,
    ProcessOwner,
)

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[T]:
        result = await db.execute(select(self.model_class).where(self.model_class.id == id))
        return result.scalar_one_or_none()

    def add(self, db: AsyncSession, obj: T) -> None:
        db.add(obj)


class DocumentRepository(BaseRepository[Document]):
    def __init__(self):
        super().__init__(Document)


class NonConformityRepository(BaseRepository[NonConformity]):
    def __init__(self):
        super().__init__(NonConformity)


class CorrectiveActionRepository(BaseRepository[CorrectiveAction]):
    def __init__(self):
        super().__init__(CorrectiveAction)


class InternalAuditRepository(BaseRepository[InternalAudit]):
    def __init__(self):
        super().__init__(InternalAudit)


class AuditChecklistItemRepository(BaseRepository[AuditChecklistItem]):
    def __init__(self):
        super().__init__(AuditChecklistItem)


class ProcessOwnerRepository(BaseRepository[ProcessOwner]):
    def __init__(self):
        super().__init__(ProcessOwner)


class ContinuousImprovementRepository(BaseRepository[ContinuousImprovement]):
    def __init__(self):
        super().__init__(ContinuousImprovement)


# Instances
document_repo = DocumentRepository()
nc_repo = NonConformityRepository()
corrective_action_repo = CorrectiveActionRepository()
audit_repo = InternalAuditRepository()
audit_checklist_repo = AuditChecklistItemRepository()
process_owner_repo = ProcessOwnerRepository()
improvement_repo = ContinuousImprovementRepository()
