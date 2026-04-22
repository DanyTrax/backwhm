from __future__ import annotations

import asyncio
from pathlib import Path
from shlex import quote

from app.services.effective_config import EffectiveIntegrationConfig, ssh_configured


def _ssh_base(cfg: EffectiveIntegrationConfig) -> list[str]:
    return [
        "ssh",
        "-i",
        cfg.whm_ssh_key_path,
        "-p",
        str(cfg.whm_ssh_port),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        f"{cfg.whm_ssh_user}@{cfg.whm_ssh_host}",
    ]


async def ssh_exec(cfg: EffectiveIntegrationConfig, remote_command: str) -> tuple[int, str, str]:
    """Run a remote shell command on WHM via SSH. Returns (code, stdout, stderr)."""
    if not ssh_configured(cfg):
        return 127, "", "SSH not configured or key missing"
    proc = await asyncio.create_subprocess_exec(
        *_ssh_base(cfg),
        remote_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out_b, err_b = await proc.communicate()
    return proc.returncode or 0, out_b.decode(errors="replace"), err_b.decode(errors="replace")


async def scp_from_remote(cfg: EffectiveIntegrationConfig, remote_path: str, local_path: Path) -> tuple[int, str]:
    if not ssh_configured(cfg):
        return 127, "SSH not configured or key missing"
    local_path.parent.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        "scp",
        "-i",
        cfg.whm_ssh_key_path,
        "-P",
        str(cfg.whm_ssh_port),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        f"{cfg.whm_ssh_user}@{cfg.whm_ssh_host}:{remote_path}",
        str(local_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    return proc.returncode or 0, err.decode(errors="replace")


async def scp_to_remote(cfg: EffectiveIntegrationConfig, local_path: Path, remote_path: str) -> tuple[int, str]:
    if not ssh_configured(cfg):
        return 127, "SSH not configured or key missing"
    proc = await asyncio.create_subprocess_exec(
        "scp",
        "-i",
        cfg.whm_ssh_key_path,
        "-P",
        str(cfg.whm_ssh_port),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        str(local_path),
        f"{cfg.whm_ssh_user}@{cfg.whm_ssh_host}:{remote_path}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    return proc.returncode or 0, err.decode(errors="replace")


async def ssh_rm(cfg: EffectiveIntegrationConfig, remote_path: str) -> tuple[int, str, str]:
    return await ssh_exec(cfg, f"rm -f -- {quote(remote_path)}")
