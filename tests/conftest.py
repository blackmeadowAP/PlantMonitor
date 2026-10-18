"""Общие фикстуры тестов."""

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from core.db import create_engine

# Тестовая БД: сервис db_test в compose (с хоста — порт 5433) или service-контейнер в CI
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://agro:agro@localhost:5433/agro_test"
)


@pytest.fixture(scope="session")
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """Движок тестовой БД PostGIS."""
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()
