"""Web auth dependencies — session cookie + CSRF protection."""

from __future__ import annotations

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.service import get_user_by_id
from app.core.config import settings
from app.core.database import get_db

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def create_session_token(user_id: int, role: str, csrf_token: str) -> str:
    """Create a signed session cookie value."""
    return _serializer.dumps({"user_id": user_id, "role": role, "csrf": csrf_token})


def decode_session_token(token: str) -> Optional[dict]:
    """Decode and validate a signed session cookie. Returns None on failure."""
    try:
        return _serializer.loads(token, max_age=settings.SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def generate_csrf_token() -> str:
    """Generate a random CSRF token."""
    import secrets
    return secrets.token_hex(32)


async def get_current_user_from_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that reads the session cookie and returns the User."""
    token: Optional[str] = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
        )

    payload = decode_session_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
        )

    user_id: int = payload["user_id"]
    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
        )
    return user


def validate_csrf(request: Request, csrf_token: str) -> None:
    """Validate CSRF token from form or HTMX header."""
    header_token = request.headers.get(settings.CSRF_HEADER)
    token = csrf_token or header_token
    if not token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")

    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not session_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No session")

    payload = decode_session_token(session_token)
    if not payload or payload.get("csrf") != token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
