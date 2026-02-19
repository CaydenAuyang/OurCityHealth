"""
Shared FastAPI dependency providers for V2.

Using a plain async generator (not @asynccontextmanager) so FastAPI's
dependency injector can call __anext__ on it directly — required for
Python 3.9 compatibility.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend_v2.db.session import async_session_factory


async def get_session() -> AsyncSession:
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
