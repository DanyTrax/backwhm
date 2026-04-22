"""Fusión de variables de entorno (.env) con ajustes guardados en BD (panel)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models import IntegrationSettings


def _pick(s: Settings, db_val: str | None, env_val: str) -> str:
    if db_val is not None and str(db_val).strip() != "":
        return str(db_val).strip()
    return env_val


def _pick_int(s: Settings, db_val: int | None, env_val: int) -> int:
    if db_val is not None:
        return int(db_val)
    return env_val


@dataclass
class EffectiveIntegrationConfig:
    """Valores efectivos para worker y comandos SSH/rclone."""

    whm_ssh_host: str
    whm_ssh_user: str
    whm_ssh_port: int
    whm_ssh_key_path: str
    whm_staging_path: str
    whm_restore_incoming: str
    rclone_remote: str
    drive_remote_prefix: str
    staging_dir: str
    file_stable_seconds: int
    worker_poll_active_seconds: int
    worker_poll_idle_seconds: int
    alert_webhook_url: str
    whm_api_host: str
    whm_api_token: str


async def load_effective(session: AsyncSession) -> EffectiveIntegrationConfig:
    s = get_settings()
    res = await session.execute(select(IntegrationSettings).where(IntegrationSettings.id == 1))
    row = res.scalar_one_or_none()

    def p(db_s: str | None, env_s: str) -> str:
        return _pick(s, db_s, env_s)

    def pi(db_i: int | None, env_i: int) -> int:
        return _pick_int(s, db_i, env_i)

    r_whm_host = p(row.whm_ssh_host if row else None, s.whm_ssh_host)
    r_whm_user = p(row.whm_ssh_user if row else None, s.whm_ssh_user)
    r_port = pi(row.whm_ssh_port if row else None, s.whm_ssh_port)
    r_key = p(row.whm_ssh_key_path if row else None, s.whm_ssh_key_path)
    r_staging = p(row.whm_staging_path if row else None, s.whm_staging_path)
    r_restore = p(row.whm_restore_incoming if row else None, s.whm_restore_incoming)
    r_clone = p(row.rclone_remote if row else None, s.rclone_remote)
    r_prefix = p(row.drive_remote_prefix if row else None, s.drive_remote_prefix)
    r_alert = p(row.alert_webhook_url if row else None, s.alert_webhook_url)
    r_api_host = p(row.whm_api_host if row else None, s.whm_api_host)
    r_api_tok = p(row.whm_api_token if row else None, s.whm_api_token)
    r_stable = pi(row.file_stable_seconds if row else None, s.file_stable_seconds)
    r_w_act = pi(row.worker_poll_active_seconds if row else None, s.worker_poll_active_seconds)
    r_w_idle = pi(row.worker_poll_idle_seconds if row else None, s.worker_poll_idle_seconds)

    return EffectiveIntegrationConfig(
        whm_ssh_host=r_whm_host,
        whm_ssh_user=r_whm_user,
        whm_ssh_port=r_port,
        whm_ssh_key_path=r_key,
        whm_staging_path=r_staging,
        whm_restore_incoming=r_restore,
        rclone_remote=r_clone,
        drive_remote_prefix=r_prefix,
        staging_dir=s.staging_dir,
        file_stable_seconds=r_stable,
        worker_poll_active_seconds=r_w_act,
        worker_poll_idle_seconds=r_w_idle,
        alert_webhook_url=r_alert,
        whm_api_host=r_api_host,
        whm_api_token=r_api_tok,
    )


def ssh_configured(cfg: EffectiveIntegrationConfig) -> bool:
    return bool(cfg.whm_ssh_host) and Path(cfg.whm_ssh_key_path).exists()
