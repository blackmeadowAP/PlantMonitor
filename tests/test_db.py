"""Тестовая БД и миграции."""

import asyncio

import pytest
from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from core.models import Base
from tests.conftest import alembic_config

pytestmark = pytest.mark.db

GIST_COLUMNS = {
    ("organizations", "location"),
    ("fields", "boundary"),
    ("fields", "centroid"),
    ("control_points", "location"),
    ("observations", "location"),
    ("foci", "location"),
}


async def test_db_connection(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:
        assert (await conn.execute(text("SELECT 1"))).scalar_one() == 1


async def test_postgis_installed_by_migration(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:
        version = (await conn.execute(text("SELECT postgis_lib_version()"))).scalar_one()
    assert version.startswith("3.")


async def test_all_tables_created(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:
        tables = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    assert set(Base.metadata.tables) <= tables


async def test_gist_indexes(db_engine: AsyncEngine) -> None:
    query = text(
        """
        SELECT t.relname, a.attname
        FROM pg_index ix
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_class t ON t.oid = ix.indrelid
        JOIN pg_am am ON am.oid = i.relam
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        WHERE am.amname = 'gist'
        """
    )
    async with db_engine.connect() as conn:
        found = {(r[0], r[1]) for r in await conn.execute(query)}
    assert found >= GIST_COLUMNS


async def test_models_match_migrations(db_engine: AsyncEngine) -> None:
    """Модели и миграции не расходятся (alembic check)."""
    await asyncio.to_thread(command.check, alembic_config())
