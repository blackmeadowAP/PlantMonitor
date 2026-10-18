"""Подключение к тестовой БД PostGIS."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.db


async def test_db_connection(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:
        assert (await conn.execute(text("SELECT 1"))).scalar_one() == 1


async def test_postgis_available(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        version = (await conn.execute(text("SELECT postgis_lib_version()"))).scalar_one()
    assert version.startswith("3.")
