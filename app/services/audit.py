from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


def new_correlation_id() -> str:
    return uuid.uuid4().hex


async def log_event(
    session: AsyncSession,
    *,
    actor_id: int | None,
    action: str,
    status: str = "info",
    source_path: str | None = None,
    dest_path: str | None = None,
    message: str | None = None,
    correlation_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> AuditLog:
    row = AuditLog(
        actor_id=actor_id,
        action=action,
        status=status,
        source_path=source_path,
        dest_path=dest_path,
        message=message,
        correlation_id=correlation_id,
        extra=extra,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
