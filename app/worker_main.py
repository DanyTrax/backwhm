"""Entry point for the drain/restore worker container."""

from __future__ import annotations

import asyncio
import logging

from app.bootstrap import ensure_admin_user
from app.config import get_settings
from app.db import SessionLocal, init_models
from app.worker import drain
from app.worker import restore_jobs

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worker")


async def loop() -> None:
    s = get_settings()
    await init_models()
    await ensure_admin_user()
    while True:
        worked = False
        try:
            async with SessionLocal() as session:
                if await restore_jobs.process_pending_restores(session):
                    worked = True
                if await drain.process_next_drain(session):
                    worked = True
        except Exception:
            log.exception("worker cycle error")
        delay = s.worker_poll_active_seconds if worked else s.worker_poll_idle_seconds
        log.info("sleep %s s (worked=%s)", delay, worked)
        await asyncio.sleep(delay)


def main() -> None:
    asyncio.run(loop())


if __name__ == "__main__":
    main()
