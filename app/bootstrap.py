from sqlalchemy import func, select

from app.config import get_settings
from app.db import SessionLocal
from app.models import User
from app.security import hash_password


async def ensure_admin_user() -> None:
    s = get_settings()
    async with SessionLocal() as session:
        n = await session.scalar(select(func.count()).select_from(User))
        if n and n > 0:
            return
        u = User(
            email=s.initial_admin_email,
            password_hash=hash_password(s.initial_admin_password),
            role="admin",
            active=True,
        )
        session.add(u)
        await session.commit()
