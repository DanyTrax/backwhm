from __future__ import annotations

import asyncio
from pathlib import Path

from app.config import get_settings


async def rclone_copyto(local_file: Path, remote_rel: str) -> tuple[int, str]:
    """Copy single file to remote `remote:prefix/remote_rel`."""
    s = get_settings()
    remote = f"{s.rclone_remote}:{s.drive_remote_prefix.rstrip('/')}/{remote_rel.lstrip('/')}"
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


async def rclone_copyfrom(remote_rel: str, local_file: Path) -> tuple[int, str]:
    s = get_settings()
    remote = f"{s.rclone_remote}:{s.drive_remote_prefix.rstrip('/')}/{remote_rel.lstrip('/')}"
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
