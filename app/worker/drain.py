from __future__ import annotations

import asyncio
import os
from pathlib import Path
from shlex import quote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ScheduledTask
from app.services import audit as audit_service
from app.services import alerts
from app.services import rclone_ops
from app.services import ssh_whm
from app.services.effective_config import load_effective, ssh_configured


async def _remote_stat(cfg, remote_path: str) -> tuple[int | None, int | None]:
    code, out, err = await ssh_whm.ssh_exec(cfg, f"stat -c '%s %Y' {quote(remote_path)} 2>/dev/null")
    if code != 0 or not out.strip():
        return None, None
    parts = out.strip().split()
    if len(parts) != 2:
        return None, None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None, None


async def list_remote_backup_files(cfg) -> list[str]:
    staging_q = quote(cfg.whm_staging_path.rstrip("/"))
    cmd = (
        f"find {staging_q} -type f \\( -name '*.tar' -o -name '*.tar.gz' "
        "-o -name '.master.meta' -o -name '*.master.meta' \\) 2>/dev/null | sort"
    )
    code, out, err = await ssh_whm.ssh_exec(cfg, cmd)
    if code != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _passes_account_filter(remote_path: str, filt: list[str] | None) -> bool:
    if not filt:
        return True
    base = os.path.basename(remote_path)
    name = base.split(".", 1)[0]
    return any(name == f or base.startswith(f + ".") for f in filt)


async def is_file_stable(cfg, remote_path: str, stable_seconds: int) -> bool:
    s1, t1 = await _remote_stat(cfg, remote_path)
    if s1 is None:
        return False
    await asyncio.sleep(stable_seconds)
    s2, t2 = await _remote_stat(cfg, remote_path)
    if s2 is None:
        return False
    return s1 == s2 and t1 == t2


async def process_next_drain(session: AsyncSession) -> bool:
    """
    Transfer one stable remote artifact to Drive and delete on WHM.
    Returns True if work was done.
    """
    cfg = await load_effective(session)
    if not ssh_configured(cfg):
        return False

    result = await session.execute(select(ScheduledTask).where(ScheduledTask.enabled.is_(True)))
    tasks = result.scalars().all()
    account_filter: list[str] | None = None
    if tasks:
        for t in tasks:
            if t.account_filter:
                account_filter = list(t.account_filter)
                break

    files = await list_remote_backup_files(cfg)
    for remote_path in files:
        if not _passes_account_filter(remote_path, account_filter):
            continue
        if not await is_file_stable(cfg, remote_path, cfg.file_stable_seconds):
            continue

        corr = audit_service.new_correlation_id()
        staging_root = cfg.whm_staging_path.rstrip("/")
        rel = remote_path[len(staging_root) :].lstrip("/")
        local_tmp = Path(cfg.staging_dir) / "pull" / rel
        local_tmp.parent.mkdir(parents=True, exist_ok=True)

        await audit_service.log_event(
            session,
            actor_id=None,
            action="drain_start",
            status="info",
            source_path=remote_path,
            dest_path=f"{cfg.rclone_remote}:{cfg.drive_remote_prefix}/{rel}",
            correlation_id=corr,
            message="Copiando desde WHM al VPS",
        )

        code, err = await ssh_whm.scp_from_remote(cfg, remote_path, local_tmp)
        if code != 0:
            await audit_service.log_event(
                session,
                actor_id=None,
                action="drain_scp_fail",
                status="error",
                source_path=remote_path,
                message=err[:2000],
                correlation_id=corr,
            )
            await alerts.send_alert(
                "drain_scp_fail",
                alerts.alert_safe_dict({"path": remote_path, "err": err[:500]}),
                webhook_url=cfg.alert_webhook_url,
            )
            continue

        rc, rerr = await rclone_ops.rclone_copyto(cfg, local_tmp, rel)
        if rc != 0:
            await audit_service.log_event(
                session,
                actor_id=None,
                action="drain_rclone_fail",
                status="error",
                dest_path=rel,
                message=rerr[:2000],
                correlation_id=corr,
            )
            await alerts.send_alert(
                "drain_rclone_fail",
                {"rel": rel, "err": rerr[:500]},
                webhook_url=cfg.alert_webhook_url,
            )
            try:
                local_tmp.unlink(missing_ok=True)
            except OSError:
                pass
            continue

        rm_code, _, rm_err = await ssh_whm.ssh_rm(cfg, remote_path)
        if rm_code != 0:
            await audit_service.log_event(
                session,
                actor_id=None,
                action="drain_rm_warn",
                status="warning",
                source_path=remote_path,
                message=rm_err[:2000],
                correlation_id=corr,
            )

        try:
            local_tmp.unlink(missing_ok=True)
        except OSError:
            pass

        await audit_service.log_event(
            session,
            actor_id=None,
            action="drain_done",
            status="success",
            source_path=remote_path,
            dest_path=f"{cfg.rclone_remote}:{cfg.drive_remote_prefix}/{rel}",
            correlation_id=corr,
        )
        return True

    return False
