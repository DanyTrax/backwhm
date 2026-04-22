from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import ensure_app_secrets, get_db
from app.deps import get_current_user, require_admin
from app.models import AppSecrets, AuditLog, User
from app.security import hash_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def _user_count(db: AsyncSession) -> int:
    n = await db.scalar(select(func.count()).select_from(User))
    return int(n or 0)


def _ensure_csrf(request: Request) -> str:
    tok = request.session.get("csrf_token")
    if not tok:
        tok = secrets.token_hex(16)
        request.session["csrf_token"] = tok
    return str(tok)


@router.get("/install", response_class=HTMLResponse)
async def install_get(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    if await _user_count(db) > 0:
        return RedirectResponse("/login", status_code=302)
    csrf = _ensure_csrf(request)
    err = request.session.pop("install_error", None)
    res = await db.execute(select(AppSecrets).where(AppSecrets.id == 1))
    secrets_row = res.scalar_one_or_none()
    if secrets_row is None:
        await ensure_app_secrets(db)
        res = await db.execute(select(AppSecrets).where(AppSecrets.id == 1))
        secrets_row = res.scalar_one_or_none()
    return templates.TemplateResponse(
        "install.html",
        {
            "request": request,
            "csrf_token": csrf,
            "user": None,
            "error": err,
            "secrets_row": secrets_row,
        },
    )


@router.post("/install/generate-webhook-secret")
async def install_generate_webhook_secret(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    csrf_token: Annotated[str, Form()],
):
    if await _user_count(db) > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No disponible")
    if csrf_token != request.session.get("csrf_token"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF")
    res = await db.execute(select(AppSecrets).where(AppSecrets.id == 1))
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Sin fila app_secrets")
    row.webhook_hmac_secret = secrets.token_urlsafe(32)
    await db.commit()
    return RedirectResponse("/install", status_code=303)


@router.get("/install/complete", response_class=HTMLResponse)
async def install_complete_get(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    if await _user_count(db) == 0:
        return RedirectResponse("/install", status_code=302)
    csrf = _ensure_csrf(request)
    return templates.TemplateResponse(
        "install_complete.html",
        {"request": request, "csrf_token": csrf, "user": None},
    )


@router.get("/setup", response_class=HTMLResponse)
async def setup_get(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    if await _user_count(db) > 0:
        return RedirectResponse("/login", status_code=302)
    return RedirectResponse("/install", status_code=302)
    csrf = _ensure_csrf(request)
    err = request.session.pop("setup_error", None)
    return templates.TemplateResponse(
        "setup.html", {"request": request, "csrf_token": csrf, "user": None, "error": err}
    )


@router.post("/setup")
async def setup_post(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password2: Annotated[str, Form()],
    csrf_token: Annotated[str, Form()],
):
    if await _user_count(db) > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ya configurado")
    if csrf_token != request.session.get("csrf_token"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF")
    if password != password2 or len(password) < 10:
        request.session["setup_error"] = "Las contraseñas deben coincidir y tener al menos 10 caracteres."
        return RedirectResponse("/setup", status_code=303)
    em = email.strip().lower()
    exists = await db.execute(select(User).where(User.email == em))
    if exists.scalar_one_or_none():
        request.session["setup_error"] = "Ese email ya está registrado."
        return RedirectResponse("/setup", status_code=303)
    u = User(email=em, password_hash=hash_password(password), role="admin", active=True)
    db.add(u)
    await db.commit()
    request.session.clear()
    request.session["csrf_token"] = secrets.token_hex(16)
    return RedirectResponse("/install/complete", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    if await _user_count(db) == 0:
        return RedirectResponse("/install", status_code=302)
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


@router.get("/settings/integrations", response_class=HTMLResponse)
async def integrations_page(
    request: Request,
    admin: Annotated[User, Depends(require_admin)],
):
    csrf = _ensure_csrf(request)
    return templates.TemplateResponse(
        "settings_integrations.html",
        {"request": request, "user": admin, "csrf_token": csrf},
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
