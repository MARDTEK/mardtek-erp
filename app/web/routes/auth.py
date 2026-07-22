"""Web auth routes — login, logout (session cookie-based)."""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import authenticate_user
from app.core.config import settings
from app.core.database import get_db
from app.web.deps import create_session_token, decode_session_token, generate_csrf_token
from app.web.utils import render

router = APIRouter(tags=["Web — Auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    """Render the login form."""
    csrf_token = generate_csrf_token()
    return render(request, "login.html", {"error": error, "csrf_token": csrf_token})


@router.post("/login")
async def login_submit(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and set session cookie."""
    user = await authenticate_user(db, username, password)
    if user is None:
        csrf_token = generate_csrf_token()
        return render(request, "login.html", {"error": "Invalid username or password", "csrf_token": csrf_token}, status_code=401)

    csrf_token = generate_csrf_token()
    session_token = create_session_token(user.id, user.role, csrf_token)

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/logout")
async def logout():
    """Clear session cookie and redirect to login."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
    return response
