"""Окружение Alembic (async, URL из настроек)."""

import asyncio
from logging.config import fileConfig

from alembic import context
from geoalchemy2 import alembic_helpers
from sqlalchemy.engine import Connection

from core.config import get_settings
from core.db import create_engine
from core.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """URL БД: явно переданный (тесты) или из настроек."""
    return config.attributes.get("database_url") or get_settings().database_url


def include_object(obj, name, type_, reflected, compare_to) -> bool:
    """Не трогать таблицы PostGIS (spatial_ref_sys и др.), которых нет в моделях."""
    if type_ == "table" and reflected and compare_to is None:
        return False
    return alembic_helpers.include_object(obj, name, type_, reflected, compare_to)


CONTEXT_OPTS = {
    "target_metadata": target_metadata,
    "include_object": include_object,
    "process_revision_directives": alembic_helpers.writer,
    "render_item": alembic_helpers.render_item,
}


def run_migrations_offline() -> None:
    """Генерация SQL без подключения к БД."""
    context.configure(url=get_url(), literal_binds=True, **CONTEXT_OPTS)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Применение миграций в рамках соединения."""
    context.configure(connection=connection, **CONTEXT_OPTS)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Применение миграций к БД."""
    engine = create_engine(get_url())
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
