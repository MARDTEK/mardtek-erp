"""Web utilities — template rendering, form helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.web.deps import decode_session_token

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _get_session(request: Request) -> Optional[Dict[str, Any]]:
    """Extract session data from cookie. No middleware needed."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        return None
    return decode_session_token(token)


def render(
    request: Request,
    template: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    status_code: int = 200,
) -> Any:
    """Render a Jinja2 template with standard context."""
    ctx = context or {}
    ctx.setdefault("request", request)

    # Extract session from cookie
    session = _get_session(request)
    if session:
        class _User:
            pass
        user = _User()
        user.id = session.get("user_id")
        user.role = session.get("role")
        ctx.setdefault("current_user", user)
        ctx.setdefault("csrf_token", session.get("csrf", ""))
    else:
        ctx.setdefault("current_user", None)
        ctx.setdefault("csrf_token", "")

    return templates.TemplateResponse(request, template, ctx, status_code=status_code)


def map_form_errors(errors: list) -> Dict[str, str]:
    """Map Pydantic validation errors to {field: message} for template display."""
    field_errors: Dict[str, str] = {}
    for error in errors:
        loc = error.get("loc", ())
        if len(loc) >= 2:
            field = str(loc[-1])
        elif loc:
            field = str(loc[0])
        else:
            field = "general"
        field_errors[field] = error.get("msg", "Invalid value")
    return field_errors
