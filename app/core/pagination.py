"""Reusable pagination utility for list endpoints.

Usage:
    from app.core.pagination import PaginationParams, paginate

    @router.get("/items", response_model=List[ItemResponse])
    async def list_items(
        page: PaginationParams = Depends(),
        db: AsyncSession = Depends(get_db),
    ):
        stmt = select(Item).order_by(Item.id)
        result = await db.execute(paginate(stmt, page))
        return list(result.scalars().all())
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from fastapi import Query

T = TypeVar("T")


@dataclass
class Pagination:
    skip: int
    limit: int


class PaginationParams:
    """FastAPI dependency that provides skip/limit for pagination.

    Default: skip=0, limit=100 (max 500).
    """

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=500, description="Max records per page"),
    ) -> None:
        self.skip = skip
        self.limit = limit


def paginate(stmt, page: Pagination) -> type:
    """Apply offset/limit pagination to a SQLAlchemy select statement."""
    return stmt.offset(page.skip).limit(page.limit)
