from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AdminUser
from app.models import User
from app.security import hash_password

router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(pattern="^(admin|operator)$")
    csrf_token: str = Field(min_length=8)


class UserPatch(BaseModel):
    active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    csrf_token: str = Field(min_length=8)


def _csrf(request: Request, token: str) -> None:
    if token != request.session.get("csrf_token"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF")


@router.get("")
async def list_users(db: Annotated[AsyncSession, Depends(get_db)], admin: AdminUser):
    res = await db.execute(select(User).order_by(User.id.asc()))
    users = res.scalars().all()
    return [
        {"id": u.id, "email": u.email, "role": u.role, "active": u.active, "created_at": u.created_at.isoformat()}
        for u in users
    ]


@router.post("")
async def create_user(
    request: Request,
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
):
    _csrf(request, body.csrf_token)
    exists = await db.execute(select(User).where(User.email == str(body.email).lower()))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ya existe")
    u = User(
        email=str(body.email).lower(),
        password_hash=hash_password(body.password),
        role=body.role,
        active=True,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return {"id": u.id, "email": u.email, "role": u.role}


@router.patch("/{user_id}")
async def patch_user(
    request: Request,
    user_id: int,
    body: UserPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
):
    _csrf(request, body.csrf_token)
    if user_id == admin.id and body.active is False:
        raise HTTPException(status_code=400, detail="No puede desactivarse a sí mismo")
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="No encontrado")
    if body.active is not None:
        u.active = body.active
    if body.password:
        u.password_hash = hash_password(body.password)
    await db.commit()
    return {"ok": True}
