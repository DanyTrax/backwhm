from __future__ import annotations

import os
from pathlib import Path
from shlex import quote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RestoreJob
from app.services import audit as audit_service
from app.services import rclone_ops
from app.services import ssh_whm
from app.services.effective_config import load_effective


async def process_pending_restores(session: AsyncSession) -> bool:
    cfg = await load_effective(session)
    res = await session.execute(
        select(RestoreJob).where(RestoreJob.status == "pending").order_by(RestoreJob.id.asc()).limit(1)
    )
    job = res.scalar_one_or_none()
    if not job:
        return False

    corr = job.correlation_id or audit_service.new_correlation_id()
    job.correlation_id = corr
    job.status = "running"
    await session.commit()

    local_dir = Path(cfg.staging_dir) / "restore" / corr
    local_dir.mkdir(parents=True, exist_ok=True)
    base_name = os.path.basename(job.drive_path)
    local_file = local_dir / base_name

    await audit_service.log_event(
        session,
        actor_id=job.created_by_id,
        action="restore_download_start",
        status="info",
        source_path=job.drive_path,
        dest_path=str(local_file),
        correlation_id=corr,
    )

    rc, err = await rclone_ops.rclone_copyfrom(cfg, job.drive_path, local_file)
    if rc != 0:
        job.status = "error"
        job.message = err[:4000]
        await session.commit()
        await audit_service.log_event(
            session,
            actor_id=job.created_by_id,
            action="restore_download_fail",
            status="error",
            message=err[:2000],
            correlation_id=corr,
        )
        return True

    remote_dir = cfg.whm_restore_incoming.rstrip("/")
    remote_file = f"{remote_dir}/{base_name}"
    await ssh_whm.ssh_exec(cfg, f"mkdir -p {quote(remote_dir)}")
    scp_code, scp_err = await ssh_whm.scp_to_remote(cfg, local_file, remote_file)
    if scp_code != 0:
        job.status = "error"
        job.message = scp_err[:4000]
        await session.commit()
        await audit_service.log_event(
            session,
            actor_id=job.created_by_id,
            action="restore_scp_fail",
            status="error",
            message=scp_err[:2000],
            correlation_id=corr,
        )
        return True

    if job.mode == "api":
        pkg = f"/usr/local/cpanel/scripts/restorepkg {quote(remote_file)}"
        code, out, err = await ssh_whm.ssh_exec(cfg, pkg)
        job.status = "success" if code == 0 else "error"
        job.message = (out + "\n" + err)[:4000]
        await session.commit()
        await audit_service.log_event(
            session,
            actor_id=job.created_by_id,
            action="restore_restorepkg",
            status="success" if code == 0 else "error",
            source_path=remote_file,
            message=job.message,
            correlation_id=corr,
        )
    else:
        job.status = "awaiting_manual"
        job.message = (
            "Archivo copiado al WHM. En WHM use «Transfer or Restore a cPanel Account» "
            f"o ejecute: /usr/local/cpanel/scripts/restorepkg {remote_file}"
        )
        await session.commit()
        await audit_service.log_event(
            session,
            actor_id=job.created_by_id,
            action="restore_assisted_ready",
            status="info",
            source_path=remote_file,
            message=job.message,
            correlation_id=corr,
        )

    try:
        local_file.unlink(missing_ok=True)
    except OSError:
        pass
    return True
