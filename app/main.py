from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.modules.commercial_sales.router import router as commercial_router
from app.modules.quality_management.router import router as quality_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Create tables on startup for development.
    # Production uses Alembic migrations — this is a safety net only.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": "0.1.0"}


app.include_router(quality_router, prefix="/api/v1/quality", tags=["Quality Management — P2"])
app.include_router(commercial_router, prefix="/api/v1/commercial", tags=["Commercial Sales — P3"])
