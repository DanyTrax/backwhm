"""Entry point for the drain/restore worker container."""

from __future__ import annotations

import asyncio
import logging

from app.config import get_settings
from app.db import SessionLocal, init_models
from app.services.effective_config import load_effective
from app.worker import drain
from app.worker import restore_jobs

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worker")


async def loop() -> None:
    await init_models()
    while True:
        worked = False
        delay_idle = get_settings().worker_poll_idle_seconds
        delay_active = get_settings().worker_poll_active_seconds
        try:
            async with SessionLocal() as session:
                cfg = await load_effective(session)
                delay_idle = cfg.worker_poll_idle_seconds
                delay_active = cfg.worker_poll_active_seconds
                if await restore_jobs.process_pending_restores(session):
                    worked = True
                if await drain.process_next_drain(session):
                    worked = True
        except Exception:
            log.exception("worker cycle error")
        delay = delay_active if worked else delay_idle
        log.info("sleep %s s (worked=%s)", delay, worked)
        await asyncio.sleep(delay)


def main() -> None:
    asyncio.run(loop())


if __name__ == "__main__":
    main()
