from __future__ import annotations

import csv
import io
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AdminUser, CurrentUser
from app.models import AuditLog
from app.services import audit as audit_service

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/export")
async def export_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(5000, ge=1, le=50000),
):
    res = await db.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit))
    rows = res.scalars().all()

    def row_dict(r: AuditLog) -> dict:
        return {
            "id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "actor_id": r.actor_id,
            "action": r.action,
            "status": r.status,
            "source_path": r.source_path,
            "dest_path": r.dest_path,
            "message": r.message,
            "correlation_id": r.correlation_id,
            "extra": r.extra,
        }

    if format == "json":
        data = json.dumps([row_dict(r) for r in rows], ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([data]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit.json"},
        )

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        ["id", "created_at", "actor_id", "action", "status", "source_path", "dest_path", "message", "correlation_id"]
    )
    for r in rows:
        w.writerow(
            [
                r.id,
                r.created_at.isoformat() if r.created_at else "",
                r.actor_id or "",
                r.action,
                r.status,
                r.source_path or "",
                r.dest_path or "",
                (r.message or "").replace("\n", " ")[:2000],
                r.correlation_id or "",
            ]
        )
    data = buf.getvalue()
    return StreamingResponse(
        iter([data]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=audit.csv"},
    )


class AuditDeleteBody(BaseModel):
    csrf_token: str = Field(min_length=8)
    before_id: int | None = None
    correlation_id: str | None = None
    purge_all: bool = False


@router.post("/delete")
async def delete_logs(
    body: AuditDeleteBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
):
    if body.csrf_token != request.session.get("csrf_token"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF")
    if body.purge_all:
        await db.execute(delete(AuditLog))
        await db.commit()
        await audit_service.log_event(
            db,
            actor_id=admin.id,
            action="audit_purge_all",
            status="warning",
            message="Purgado completo de auditoría",
        )
        return {"deleted": "all"}
    stmt = delete(AuditLog)
    if body.before_id is not None:
        stmt = stmt.where(AuditLog.id <= body.before_id)
    if body.correlation_id:
        stmt = stmt.where(AuditLog.correlation_id == body.correlation_id)
    res = await db.execute(stmt)
    await db.commit()
    await audit_service.log_event(
        db,
        actor_id=admin.id,
        action="audit_delete_filtered",
        status="info",
        message=f"Filtrado before_id={body.before_id} correlation={body.correlation_id}",
    )
    return {"deleted_rows": res.rowcount}
