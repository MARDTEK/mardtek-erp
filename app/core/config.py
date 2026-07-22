from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "MARDTEK ERP"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mardtek_erp"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@localhost:5432/mardtek_erp"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://mard:mardtek_erp_2026@localhost:5433/mardtek_erp_test"

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SECRET_KEY: str = "change-me-session-secret-in-production"
    SESSION_MAX_AGE: int = 28800  # 8 hours in seconds
    SESSION_COOKIE_NAME: str = "mardtek_session"
    CSRF_HEADER: str = "X-CSRF-Token"

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
