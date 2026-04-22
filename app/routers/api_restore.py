from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AdminUser
from app.models import RestoreJob
from app.services import audit as audit_service

router = APIRouter(prefix="/api/restore-jobs", tags=["restore"])


class RestoreCreate(BaseModel):
    drive_path: str = Field(min_length=4, max_length=1024)
    target_username: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    mode: str = Field(default="assisted", pattern="^(assisted|api)$")
    csrf_token: str = Field(min_length=8)


def _csrf(request: Request, token: str) -> None:
    if token != request.session.get("csrf_token"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF")


@router.post("")
async def create_restore_job(
    request: Request,
    body: RestoreCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
):
    _csrf(request, body.csrf_token)
    corr = audit_service.new_correlation_id()
    job = RestoreJob(
        created_by_id=admin.id,
        drive_path=body.drive_path.strip(),
        target_username=body.target_username,
        mode=body.mode,
        status="pending",
        correlation_id=corr,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await audit_service.log_event(
        db,
        actor_id=admin.id,
        action="restore_job_created",
        status="info",
        source_path=body.drive_path,
        message=f"Job {job.id} mode={body.mode}",
        correlation_id=corr,
    )
    return {"id": job.id, "status": job.status, "correlation_id": corr}
