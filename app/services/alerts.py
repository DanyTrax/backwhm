from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import get_settings


async def send_alert(title: str, body: dict[str, Any]) -> None:
    url = get_settings().alert_webhook_url
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(url, json={"title": title, "body": body})
    except Exception:
        # Never raise from alert path
        pass


def alert_safe_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Remove obvious secret keys from outbound payloads."""
    redacted = dict(d)
    for k in list(redacted.keys()):
        if any(s in k.lower() for s in ("password", "token", "secret", "key")):
            redacted[k] = "***"
    return redacted
