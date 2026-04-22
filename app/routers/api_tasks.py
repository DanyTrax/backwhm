from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AdminUser, CurrentUser
from app.models import ScheduledTask

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    cron: str = Field(min_length=9, max_length=128)
    task_type: str = Field(default="drain_scan", max_length=64)
    account_filter: list[str] | None = None
    max_concurrent: int = Field(default=1, ge=1, le=4)
    enabled: bool = True
    csrf_token: str = Field(min_length=8)


class TaskPatch(BaseModel):
    enabled: bool | None = None
    cron: str | None = Field(default=None, max_length=128)
    account_filter: list[str] | None = None
    csrf_token: str = Field(min_length=8)


def _csrf(request: Request, token: str) -> None:
    if token != request.session.get("csrf_token"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF")


@router.get("")
async def list_tasks(db: Annotated[AsyncSession, Depends(get_db)], user: CurrentUser):
    res = await db.execute(select(ScheduledTask).order_by(ScheduledTask.id.asc()))
    tasks = res.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "cron": t.cron,
            "task_type": t.task_type,
            "account_filter": t.account_filter,
            "max_concurrent": t.max_concurrent,
            "enabled": t.enabled,
        }
        for t in tasks
    ]


@router.post("")
async def create_task(
    request: Request,
    body: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
):
    _csrf(request, body.csrf_token)
    t = ScheduledTask(
        name=body.name,
        cron=body.cron,
        task_type=body.task_type,
        account_filter=body.account_filter,
        max_concurrent=body.max_concurrent,
        enabled=body.enabled,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": t.id}


@router.patch("/{task_id}")
async def patch_task(
    request: Request,
    task_id: int,
    body: TaskPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
):
    _csrf(request, body.csrf_token)
    res = await db.execute(select(ScheduledTask).where(ScheduledTask.id == task_id))
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="No encontrado")
    if body.enabled is not None:
        t.enabled = body.enabled
    if body.cron is not None:
        t.cron = body.cron
    if body.account_filter is not None:
        t.account_filter = body.account_filter
    await db.commit()
    return {"ok": True}
