"""Подключение к БД: async-движок и фабрика сессий."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import get_settings


def create_engine(url: str) -> AsyncEngine:
    """Создаёт async-движок SQLAlchemy."""
    return create_async_engine(url, pool_pre_ping=True)


@lru_cache
def get_engine() -> AsyncEngine:
    """Движок основной БД (один на процесс)."""
    return create_engine(get_settings().database_url)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Фабрика сессий основной БД."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Сессия БД для зависимостей FastAPI и middleware бота."""
    async with get_sessionmaker()() as session:
        yield session
