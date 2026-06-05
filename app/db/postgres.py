"""
PostgreSQL / TimescaleDB async engine — lazily initialized.

The engine is only constructed when `settings.TIMESCALE_ENABLED` is true.
This keeps the app fully functional in dev / preview environments where
no Postgres instance is provisioned.
"""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.db.base import Base

_engine: Optional[AsyncEngine] = None
_SessionLocal: Optional[async_sessionmaker] = None


def _async_url() -> str:
    """Coerce a sync psycopg2 URL into an asyncpg URL for SQLAlchemy async."""
    url = settings.POSTGRES_URL
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_engine() -> Optional[AsyncEngine]:
    """Return the cached engine, creating it on first access if the flag is on."""
    global _engine, _SessionLocal
    if not settings.TIMESCALE_ENABLED:
        return None
    if _engine is None:
        _engine = create_async_engine(_async_url(), echo=settings.DEBUG, future=True, pool_pre_ping=True)
        _SessionLocal = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _engine


async def get_postgres_session() -> AsyncGenerator[Optional[AsyncSession], None]:
    """FastAPI dependency — yields a session, or None when Timescale is disabled."""
    if not settings.TIMESCALE_ENABLED:
        yield None
        return
    get_engine()  # ensures _SessionLocal is built
    assert _SessionLocal is not None
    async with _SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_postgres_db() -> None:
    """
    Create tables (idempotent). Hypertable conversion is left to Alembic migration
    since `create_extension` + `create_hypertable` are TimescaleDB-specific.
    Safe no-op when the flag is off.
    """
    if not settings.TIMESCALE_ENABLED:
        return
    engine = get_engine()
    assert engine is not None
    # Trigger model registration via metadata
    from app.models import postgres as _models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def healthcheck() -> dict:
    """Lightweight readiness check used by the admin status endpoint."""
    if not settings.TIMESCALE_ENABLED:
        return {"enabled": False, "reachable": False, "detail": "TIMESCALE_ENABLED is off"}
    try:
        engine = get_engine()
        assert engine is not None
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"enabled": True, "reachable": True, "detail": "ok"}
    except Exception as exc:  # noqa: BLE001 - bubble up reason to operator
        return {"enabled": True, "reachable": False, "detail": str(exc)[:200]}
