from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.modules.commercial_sales.router import router as commercial_router
from app.modules.pmo_projects.router import router as pmo_projects_router
from app.modules.training_services.router import router as training_router
from app.modules.strategic_planning.router import router as strategic_router
from app.modules.quality_management.router import router as quality_router
from app.modules.tech_development.router import router as tech_development_router
from app.modules.procurement.router import router as procurement_router
from app.modules.analytics_performance.router import router as analytics_router
from app.modules.customer_experience.router import router as customer_experience_router
from app.modules.infrastructure_it.router import router as infrastructure_router
from app.modules.human_resources.router import router as human_resources_router


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
app.include_router(strategic_router, prefix="/api/v1/strategic", tags=["Strategic Management — P1"])
app.include_router(tech_development_router, prefix="/api/v1/development", tags=["Design & Development — P4"])
app.include_router(pmo_projects_router, prefix="/api/v1/projects", tags=["Project Implementation & Execution — P5"])
app.include_router(training_router, prefix="/api/v1/training", tags=["Training & Human Development — P6"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Data Analysis & Performance Evaluation — P11"])
app.include_router(customer_experience_router, prefix="/api/v1/customer-satisfaction", tags=["Customer Satisfaction — P10"])
app.include_router(infrastructure_router, prefix="/api/v1/infrastructure", tags=["Infrastructure & Technology — P8"])
app.include_router(human_resources_router, prefix="/api/v1/hr", tags=["HR Management — P7"])
app.include_router(procurement_router, prefix="/api/v1/procurement", tags=["Procurement & Supplier Management — P9"])
