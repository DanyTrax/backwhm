from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.db import SessionLocal, init_models
from app.middleware import SecurityHeadersMiddleware
from app.routers import api_audit, api_integration, api_restore, api_tasks, api_users, auth, pages, webhooks

log = logging.getLogger("app.main")


async def _bootstrap_session_secret() -> str:
    await init_models()
    from sqlalchemy import select

    from app.models import AppSecrets

    async with SessionLocal() as db:
        res = await db.execute(select(AppSecrets).where(AppSecrets.id == 1))
        row = res.scalar_one_or_none()
        if row and row.session_secret.strip():
            return row.session_secret.strip()
    return get_settings().session_secret


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Las tablas y app_secrets se crean en create_app() antes del SessionMiddleware.
    yield


def create_app() -> FastAPI:
    try:
        session_secret = asyncio.run(_bootstrap_session_secret())
    except Exception as e:
        log.warning("bootstrap DB falló (%s); se usa SESSION_SECRET del entorno", e)
        session_secret = get_settings().session_secret

    app = FastAPI(title="WHM Backup Panel", lifespan=lifespan)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(SessionMiddleware, secret_key=session_secret, same_site="lax", https_only=False)

    app.include_router(auth.router)
    app.include_router(webhooks.router)
    app.include_router(api_integration.router)
    app.include_router(api_audit.router)
    app.include_router(api_users.router)
    app.include_router(api_restore.router)
    app.include_router(api_tasks.router)
    app.include_router(pages.router)

    @app.get("/health")
    async def health():
        return JSONResponse({"status": "ok"})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        accept = request.headers.get("accept", "")
        if exc.status_code == 401 and "text/html" in accept and not request.url.path.startswith("/api"):
            return RedirectResponse(url="/login", status_code=302)
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return app


app = create_app()
