from __future__ import annotations

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.config import get_settings
from app.db import SessionLocal
from app.services import audit as audit_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
log = logging.getLogger("webhooks")


def _verify_hmac(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    sent = signature_header.split("=", 1)[1].strip()
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, sent)


@router.post("/pkgacct")
async def pkgacct_hook(request: Request) -> dict:
    s = get_settings()
    body = await request.body()
    if s.webhook_hmac_secret:
        sig = request.headers.get("X-Signature") or request.headers.get("X-Hub-Signature-256")
        if not _verify_hmac(s.webhook_hmac_secret, body, sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma inválida")
    try:
        payload = json.loads(body.decode() or "{}")
    except json.JSONDecodeError:
        payload = {}

    user = payload.get("user") or payload.get("username")
    tarball = payload.get("tarball") or payload.get("path")
    async with SessionLocal() as session:
        await audit_service.log_event(
            session,
            actor_id=None,
            action="hook_pkgacct",
            status="info",
            source_path=str(tarball) if tarball else None,
            message=f"Usuario cPanel reportado: {user}",
            extra=payload if isinstance(payload, dict) else None,
        )
    log.info("pkgacct hook user=%s tarball=%s", user, tarball)
    return {"ok": True}
