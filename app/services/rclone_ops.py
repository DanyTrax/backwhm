from __future__ import annotations

import asyncio
from pathlib import Path

from app.services.effective_config import EffectiveIntegrationConfig


async def rclone_copyto(cfg: EffectiveIntegrationConfig, local_file: Path, remote_rel: str) -> tuple[int, str]:
    """Copy single file to remote `remote:prefix/remote_rel`."""
    remote = f"{cfg.rclone_remote}:{cfg.drive_remote_prefix.rstrip('/')}/{remote_rel.lstrip('/')}"
    proc = await asyncio.create_subprocess_exec(
        "rclone",
        "copyto",
        str(local_file),
        remote,
        "--retries",
        "5",
        "--low-level-retries",
        "10",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    return proc.returncode or 0, err.decode(errors="replace")


async def rclone_copyfrom(cfg: EffectiveIntegrationConfig, remote_rel: str, local_file: Path) -> tuple[int, str]:
    remote = f"{cfg.rclone_remote}:{cfg.drive_remote_prefix.rstrip('/')}/{remote_rel.lstrip('/')}"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        "rclone",
        "copyto",
        remote,
        str(local_file),
        "--retries",
        "5",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    return proc.returncode or 0, err.decode(errors="replace")
