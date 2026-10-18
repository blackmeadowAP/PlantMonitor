"""Общие фикстуры тестов."""

import asyncio
import os
from collections.abc import AsyncIterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker

from core.db import create_engine

# Тестовая БД: сервис db_test в compose (с хоста — порт 5433) или service-контейнер в CI
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://agro:agro@localhost:5433/agro_test"
)


def alembic_config() -> Config:
    """Конфиг Alembic, направленный на тестовую БД."""
    cfg = Config("alembic.ini")
    cfg.attributes["database_url"] = TEST_DATABASE_URL
    return cfg


@pytest.fixture(scope="session")
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """Движок тестовой БД со свежей схемой: downgrade base → upgrade head."""
    cfg = alembic_config()
    # env.py запускает свой event loop — выполняем миграции в отдельном потоке
    await asyncio.to_thread(command.downgrade, cfg, "base")
    await asyncio.to_thread(command.upgrade, cfg, "head")
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_conn(db_engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    """Соединение в транзакции, которая откатывается после теста."""
    async with db_engine.connect() as conn:
        trans = await conn.begin()
        yield conn
        await trans.rollback()


@pytest.fixture
def sessionmaker(db_conn: AsyncConnection) -> async_sessionmaker[AsyncSession]:
    """Фабрика сессий поверх тестовой транзакции: commit внутри теста — это savepoint."""
    return async_sessionmaker(
        bind=db_conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )


@pytest.fixture
async def session(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    """Сессия тестовой БД; все изменения откатываются после теста."""
    async with sessionmaker() as s:
        yield s
