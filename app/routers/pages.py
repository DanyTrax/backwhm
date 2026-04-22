from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user, require_admin
from app.models import AuditLog, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _ensure_csrf(request: Request) -> str:
    tok = request.session.get("csrf_token")
    if not tok:
        tok = secrets.token_hex(16)
        request.session["csrf_token"] = tok
    return str(tok)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    csrf = _ensure_csrf(request)
    return templates.TemplateResponse(
        "login.html", {"request": request, "csrf_token": csrf, "user": None}
    )


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    csrf = _ensure_csrf(request)
    res = await db.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(15))
    recent = res.scalars().all()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "csrf_token": csrf, "recent": recent},
    )


@router.get("/audit", response_class=HTMLResponse)
async def audit_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = 1,
):
    csrf = _ensure_csrf(request)
    page = max(1, page)
    per = 50
    res = await db.execute(
        select(AuditLog).order_by(AuditLog.id.desc()).offset((page - 1) * per).limit(per)
    )
    rows = res.scalars().all()
    return templates.TemplateResponse(
        "audit.html",
        {
            "request": request,
            "user": user,
            "csrf_token": csrf,
            "rows": rows,
            "page": page,
            "is_admin": user.role == "admin",
        },
    )


@router.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    csrf = _ensure_csrf(request)
    res = await db.execute(select(User).order_by(User.id.asc()))
    users = res.scalars().all()
    return templates.TemplateResponse(
        "users.html",
        {"request": request, "user": admin, "csrf_token": csrf, "users": users},
    )


@router.get("/docs", response_class=HTMLResponse)
async def docs_page(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
):
    csrf = _ensure_csrf(request)
    return templates.TemplateResponse("docs.html", {"request": request, "user": user, "csrf_token": csrf})


@router.get("/restore", response_class=HTMLResponse)
async def restore_page(
    request: Request,
    admin: Annotated[User, Depends(require_admin)],
):
    csrf = _ensure_csrf(request)
    return templates.TemplateResponse("restore.html", {"request": request, "user": admin, "csrf_token": csrf})


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
):
    csrf = _ensure_csrf(request)
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "user": user, "csrf_token": csrf, "is_admin": user.role == "admin"},
    )
