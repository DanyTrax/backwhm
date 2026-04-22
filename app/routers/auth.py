from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.security import verify_password

router = APIRouter()


def _csrf_check(request: Request, token: str | None) -> None:
    if not token or token != request.session.get("csrf_token"):
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF")


@router.post("/login")
async def login(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    csrf_token: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _csrf_check(request, csrf_token)
    res = await db.execute(select(User).where(User.email == email.strip().lower(), User.active.is_(True)))
    user = res.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["csrf_token"] = secrets.token_hex(16)
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
async def logout(request: Request, csrf_token: Annotated[str, Form()]):
    _csrf_check(request, csrf_token)
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
