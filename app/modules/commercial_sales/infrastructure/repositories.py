from typing import Optional, TypeVar, Generic, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commercial_sales.domain.models import (
    Contract,
    Lead,
    Onboarding,
    Proposal,
    SaasSubscription,
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


class LeadRepository(BaseRepository[Lead]):
    def __init__(self):
        super().__init__(Lead)


class ProposalRepository(BaseRepository[Proposal]):
    def __init__(self):
        super().__init__(Proposal)


class ContractRepository(BaseRepository[Contract]):
    def __init__(self):
        super().__init__(Contract)


class SubscriptionRepository(BaseRepository[SaasSubscription]):
    def __init__(self):
        super().__init__(SaasSubscription)


class OnboardingRepository(BaseRepository[Onboarding]):
    def __init__(self):
        super().__init__(Onboarding)

# Singletons or instantiable as needed
lead_repo = LeadRepository()
proposal_repo = ProposalRepository()
contract_repo = ContractRepository()
subscription_repo = SubscriptionRepository()
onboarding_repo = OnboardingRepository()
