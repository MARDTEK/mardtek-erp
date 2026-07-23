from typing import Optional, TypeVar, Generic, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.strategic_planning.domain.models import (
    ManagementReviewReport,
    MarketingPlan,
    QmsScope,
    QualityObjective,
    QualityPolicy,
    StrategyReview,
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


class QualityPolicyRepository(BaseRepository[QualityPolicy]):
    def __init__(self):
        super().__init__(QualityPolicy)


class QualityObjectiveRepository(BaseRepository[QualityObjective]):
    def __init__(self):
        super().__init__(QualityObjective)


class MarketingPlanRepository(BaseRepository[MarketingPlan]):
    def __init__(self):
        super().__init__(MarketingPlan)


class StrategyReviewRepository(BaseRepository[StrategyReview]):
    def __init__(self):
        super().__init__(StrategyReview)


class ManagementReviewReportRepository(BaseRepository[ManagementReviewReport]):
    def __init__(self):
        super().__init__(ManagementReviewReport)


class QmsScopeRepository(BaseRepository[QmsScope]):
    def __init__(self):
        super().__init__(QmsScope)


# Instances
policy_repo = QualityPolicyRepository()
objective_repo = QualityObjectiveRepository()
marketing_plan_repo = MarketingPlanRepository()
strategy_review_repo = StrategyReviewRepository()
management_review_repo = ManagementReviewReportRepository()
qms_scope_repo = QmsScopeRepository()
