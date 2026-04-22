from __future__ import annotations

import asyncio
from pathlib import Path
from shlex import quote

from app.config import get_settings


def _ssh_base() -> list[str]:
    s = get_settings()
    key = s.whm_ssh_key_path
    return [
        "ssh",
        "-i",
        key,
        "-p",
        str(s.whm_ssh_port),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        f"{s.whm_ssh_user}@{s.whm_ssh_host}",
    ]


async def ssh_exec(remote_command: str) -> tuple[int, str, str]:
    """Run a remote shell command on WHM via SSH. Returns (code, stdout, stderr)."""
    s = get_settings()
    if not s.whm_ssh_host or not Path(s.whm_ssh_key_path).exists():
        return 127, "", "SSH not configured or key missing"
    proc = await asyncio.create_subprocess_exec(
        *_ssh_base(),
        remote_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out_b, err_b = await proc.communicate()
    return proc.returncode or 0, out_b.decode(errors="replace"), err_b.decode(errors="replace")


async def scp_from_remote(remote_path: str, local_path: Path) -> tuple[int, str]:
    s = get_settings()
    local_path.parent.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        "scp",
        "-i",
        s.whm_ssh_key_path,
        "-P",
        str(s.whm_ssh_port),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        f"{s.whm_ssh_user}@{s.whm_ssh_host}:{remote_path}",
        str(local_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    return proc.returncode or 0, err.decode(errors="replace")


async def scp_to_remote(local_path: Path, remote_path: str) -> tuple[int, str]:
    s = get_settings()
    proc = await asyncio.create_subprocess_exec(
        "scp",
        "-i",
        s.whm_ssh_key_path,
        "-P",
        str(s.whm_ssh_port),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        str(local_path),
        f"{s.whm_ssh_user}@{s.whm_ssh_host}:{remote_path}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    return proc.returncode or 0, err.decode(errors="replace")


async def ssh_rm(remote_path: str) -> tuple[int, str, str]:
    return await ssh_exec(f"rm -f -- {quote(remote_path)}")
