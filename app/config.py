from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://backupwhm:changeme_pg@localhost:5432/backupwhm"
    session_secret: str = "change-me-session-secret-min-32-chars!!"
    csrf_secret: str = "change-me-csrf-secret-min-32-chars!!"

    initial_admin_email: str = "admin@local"
    initial_admin_password: str = "admin123change"

    whm_ssh_host: str = ""
    whm_ssh_user: str = "root"
    whm_ssh_port: int = 22
    whm_ssh_key_path: str = "/secrets/whm_rsa"
    whm_staging_path: str = "/home/backup"
    whm_restore_incoming: str = "/root/incoming_restore"

    rclone_remote: str = "gdrive"
    drive_remote_prefix: str = "WHM03_BACKUP"

    webhook_hmac_secret: str = ""

    worker_poll_active_seconds: int = 120
    worker_poll_idle_seconds: int = 900
    file_stable_seconds: int = 180
    drain_max_retries: int = 5
    drain_retry_base_seconds: int = 60

    alert_webhook_url: str = ""

    whm_api_host: str = ""
    whm_api_token: str = ""

    staging_dir: str = "/data/staging"


@lru_cache
def get_settings() -> Settings:
    return Settings()
