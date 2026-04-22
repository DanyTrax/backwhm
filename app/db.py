import secrets
from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def ensure_app_secrets(session: AsyncSession) -> None:
    from app.models import AppSecrets

    res = await session.execute(select(AppSecrets).where(AppSecrets.id == 1))
    if res.scalar_one_or_none() is not None:
        return
    session.add(
        AppSecrets(
            id=1,
            session_secret=secrets.token_urlsafe(48),
            webhook_hmac_secret=None,
        )
    )
    await session.commit()


async def init_models() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await ensure_app_secrets(session)
