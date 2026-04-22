from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.bootstrap import ensure_admin_user
from app.config import get_settings
from app.db import init_models
from app.middleware import SecurityHeadersMiddleware
from app.routers import api_audit, api_restore, api_tasks, api_users, auth, pages, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    await ensure_admin_user()
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="WHM Backup Panel", lifespan=lifespan)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(SessionMiddleware, secret_key=s.session_secret, same_site="lax", https_only=False)

    app.include_router(auth.router)
    app.include_router(webhooks.router)
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
