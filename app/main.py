"""FastAPI application — MARDTEK ERP."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.auth.models import User
from app.auth.router import router as auth_router
from app.auth.service import hash_password
from app.core.config import settings
from app.core.database import Base, async_session_factory, dispose_engine, get_engine
from app.web.routes.auth import router as web_auth_router
from app.web.routes.dashboard import router as web_dashboard_router
from app.web.routes.quality import router as web_quality_router
from app.web.routes.strategic import router as web_strategic_router
from app.web.routes.commercial import router as web_commercial_router
from app.web.routes.tech_dev import router as web_tech_dev_router
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


async def seed_admin() -> None:
    """Create default admin user if it doesn't exist."""
    factory = async_session_factory()
    async with factory() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none() is None:
            admin = User(
                username="admin",
                email="admin@mardtek.com",
                hashed_password=hash_password("admin123"),
                role="admin",
            )
            session.add(admin)
            await session.commit()
            print("✅ Seeded admin user (admin / admin123)")
        else:
            print("ℹ️  Admin user already exists, skipping seed")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Create tables on startup for development.
    # Production uses Alembic migrations — this is a safety net only.
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_admin()
    yield
    await dispose_engine()


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ────────────────────────────────────────────────────────
_static_dir = Path(__file__).resolve().parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": "0.1.0"}


app.include_router(auth_router)
app.include_router(web_auth_router)  # Login/logout HTML routes
app.include_router(web_dashboard_router)  # Dashboard HTML route
app.include_router(web_quality_router)  # Quality Management HTML routes
app.include_router(web_strategic_router)  # Strategic Planning HTML routes
app.include_router(web_commercial_router)  # Commercial Sales HTML routes
app.include_router(web_tech_dev_router)  # Tech Development HTML routes
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


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to login page."""
    return RedirectResponse(url="/login", status_code=302)
