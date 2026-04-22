from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AppSecrets(Base):
    """Fila única id=1: claves generadas en la BD (sin depender de .env en Dockge)."""

    __tablename__ = "app_secrets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    session_secret: Mapped[str] = mapped_column(Text)
    webhook_hmac_secret: Mapped[str | None] = mapped_column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="operator")  # admin | operator
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class IntegrationSettings(Base):
    """Fila única id=1: integración WHM/Drive editable desde el panel (toma precedencia sobre .env si el campo no está vacío)."""

    __tablename__ = "integration_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    whm_ssh_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    whm_ssh_user: Mapped[str | None] = mapped_column(String(64), nullable=True)
    whm_ssh_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    whm_ssh_key_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    whm_staging_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    whm_restore_incoming: Mapped[str | None] = mapped_column(String(512), nullable=True)

    rclone_remote: Mapped[str | None] = mapped_column(String(128), nullable=True)
    drive_remote_prefix: Mapped[str | None] = mapped_column(String(512), nullable=True)

    alert_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_stable_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    worker_poll_active_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    worker_poll_idle_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    whm_api_host: Mapped[str | None] = mapped_column(String(512), nullable=True)
    whm_api_token: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    dest_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="info", index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    actor = relationship("User")


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    cron: Mapped[str] = mapped_column(String(128))
    task_type: Mapped[str] = mapped_column(String(64), default="drain_scan")
    account_filter: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    max_concurrent: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class RestoreJob(Base):
    __tablename__ = "restore_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    drive_path: Mapped[str] = mapped_column(Text)
    target_username: Mapped[str] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(32), default="assisted")  # assisted | api
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
