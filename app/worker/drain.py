from __future__ import annotations

import asyncio
import os
from pathlib import Path
from shlex import quote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import ScheduledTask
from app.services import audit as audit_service
from app.services import alerts
from app.services import rclone_ops
from app.services import ssh_whm


async def _remote_stat(path: str) -> tuple[int | None, int | None]:
    """Return (size, mtime_epoch) or None if failed."""
    code, out, err = await ssh_whm.ssh_exec(f"stat -c '%s %Y' {quote(path)} 2>/dev/null")
    if code != 0 or not out.strip():
        return None, None
    parts = out.strip().split()
    if len(parts) != 2:
        return None, None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None, None


async def list_remote_backup_files() -> list[str]:
    s = get_settings()
    staging_q = quote(s.whm_staging_path.rstrip("/"))
    cmd = (
        f"find {staging_q} -type f \\( -name '*.tar' -o -name '*.tar.gz' "
        "-o -name '.master.meta' -o -name '*.master.meta' \\) 2>/dev/null | sort"
    )
    code, out, err = await ssh_whm.ssh_exec(cmd)
    if code != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _passes_account_filter(remote_path: str, filt: list[str] | None) -> bool:
    if not filt:
        return True
    base = os.path.basename(remote_path)
    name = base.split(".", 1)[0]
    return any(name == f or base.startswith(f + ".") for f in filt)


async def is_file_stable(remote_path: str, stable_seconds: int) -> bool:
    s1, t1 = await _remote_stat(remote_path)
    if s1 is None:
        return False
    await asyncio.sleep(stable_seconds)
    s2, t2 = await _remote_stat(remote_path)
    if s2 is None:
        return False
    return s1 == s2 and t1 == t2


async def process_next_drain(session: AsyncSession) -> bool:
    """
    Transfer one stable remote artifact to Drive and delete on WHM.
    Returns True if work was done.
    """
    s = get_settings()
    if not s.whm_ssh_host or not Path(s.whm_ssh_key_path).exists():
        return False

    result = await session.execute(select(ScheduledTask).where(ScheduledTask.enabled.is_(True)))
    tasks = result.scalars().all()
    account_filter: list[str] | None = None
    if tasks:
        # Use first enabled task filter if any defines filter
        for t in tasks:
            if t.account_filter:
                account_filter = list(t.account_filter)
                break

    files = await list_remote_backup_files()
    for remote_path in files:
        if not _passes_account_filter(remote_path, account_filter):
            continue
        if not await is_file_stable(remote_path, s.file_stable_seconds):
            continue

        corr = audit_service.new_correlation_id()
        staging_root = s.whm_staging_path.rstrip("/")
        rel = remote_path[len(staging_root) :].lstrip("/")
        local_tmp = Path(s.staging_dir) / "pull" / rel
        local_tmp.parent.mkdir(parents=True, exist_ok=True)

        await audit_service.log_event(
            session,
            actor_id=None,
            action="drain_start",
            status="info",
            source_path=remote_path,
            dest_path=f"{s.rclone_remote}:{s.drive_remote_prefix}/{rel}",
            correlation_id=corr,
            message="Copiando desde WHM al VPS",
        )

        code, err = await ssh_whm.scp_from_remote(remote_path, local_tmp)
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
            )
            continue

        rc, rerr = await rclone_ops.rclone_copyto(local_tmp, rel)
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
            await alerts.send_alert("drain_rclone_fail", {"rel": rel, "err": rerr[:500]})
            try:
                local_tmp.unlink(missing_ok=True)
            except OSError:
                pass
            continue

        rm_code, _, rm_err = await ssh_whm.ssh_rm(remote_path)
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
            dest_path=f"{s.rclone_remote}:{s.drive_remote_prefix}/{rel}",
            correlation_id=corr,
        )
        return True

    return False
