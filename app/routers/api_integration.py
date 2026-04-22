from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AdminUser
from app.models import IntegrationSettings
from app.services import audit as audit_service
from app.services.effective_config import load_effective

router = APIRouter(prefix="/api/integration", tags=["integration"])


class IntegrationPayload(BaseModel):
    csrf_token: str = Field(min_length=8)
    whm_ssh_host: str | None = None
    whm_ssh_user: str | None = None
    whm_ssh_port: int | None = None
    whm_ssh_key_path: str | None = None
    whm_staging_path: str | None = None
    whm_restore_incoming: str | None = None
    rclone_remote: str | None = None
    drive_remote_prefix: str | None = None
    alert_webhook_url: str | None = None
    file_stable_seconds: int | None = None
    worker_poll_active_seconds: int | None = None
    worker_poll_idle_seconds: int | None = None
    whm_api_host: str | None = None
    whm_api_token: str | None = None


def _csrf(request: Request, token: str) -> None:
    if token != request.session.get("csrf_token"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF")


def _mask_token(t: str | None) -> str | None:
    if not t:
        return None
    if len(t) <= 8:
        return "***"
    return t[:4] + "…" + t[-4:]


@router.get("")
async def get_integration(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
):
    eff = await load_effective(db)
    res = await db.execute(select(IntegrationSettings).where(IntegrationSettings.id == 1))
    row = res.scalar_one_or_none()
    data: dict[str, Any] = {
        "effective": {
            "whm_ssh_host": eff.whm_ssh_host,
            "whm_ssh_user": eff.whm_ssh_user,
            "whm_ssh_port": eff.whm_ssh_port,
            "whm_ssh_key_path": eff.whm_ssh_key_path,
            "whm_staging_path": eff.whm_staging_path,
            "whm_restore_incoming": eff.whm_restore_incoming,
            "rclone_remote": eff.rclone_remote,
            "drive_remote_prefix": eff.drive_remote_prefix,
            "alert_webhook_url": eff.alert_webhook_url or "",
            "file_stable_seconds": eff.file_stable_seconds,
            "worker_poll_active_seconds": eff.worker_poll_active_seconds,
            "worker_poll_idle_seconds": eff.worker_poll_idle_seconds,
            "whm_api_host": eff.whm_api_host or "",
            "whm_api_token_masked": _mask_token(eff.whm_api_token) if eff.whm_api_token else "",
        },
        "stored": {},
    }
    if row:
        data["stored"] = {
            "whm_ssh_host": row.whm_ssh_host,
            "whm_ssh_user": row.whm_ssh_user,
            "whm_ssh_port": row.whm_ssh_port,
            "whm_ssh_key_path": row.whm_ssh_key_path,
            "whm_staging_path": row.whm_staging_path,
            "whm_restore_incoming": row.whm_restore_incoming,
            "rclone_remote": row.rclone_remote,
            "drive_remote_prefix": row.drive_remote_prefix,
            "alert_webhook_url": row.alert_webhook_url,
            "file_stable_seconds": row.file_stable_seconds,
            "worker_poll_active_seconds": row.worker_poll_active_seconds,
            "worker_poll_idle_seconds": row.worker_poll_idle_seconds,
            "whm_api_host": row.whm_api_host,
            "whm_api_token_masked": _mask_token(row.whm_api_token) if row.whm_api_token else None,
        }
    return data


@router.post("")
async def save_integration(
    request: Request,
    body: IntegrationPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
):
    _csrf(request, body.csrf_token)
    res = await db.execute(select(IntegrationSettings).where(IntegrationSettings.id == 1))
    row = res.scalar_one_or_none()
    if not row:
        row = IntegrationSettings(id=1)
        db.add(row)

    payload = body.model_dump(exclude={"csrf_token"}, exclude_unset=True)
    for k, v in payload.items():
        if not hasattr(row, k):
            continue
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            setattr(row, k, None)
            continue
        setattr(row, k, v)

    row.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await audit_service.log_event(
        db,
        actor_id=admin.id,
        action="integration_settings_saved",
        status="info",
        message="Integración WHM/Drive actualizada desde el panel",
    )
    return {"ok": True}
