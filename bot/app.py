"""Сборка диспетчера бота."""

from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.handlers import admin, agronomist, common, fallback, superuser
from bot.middlewares import DbSessionMiddleware, UserMiddleware


def create_dispatcher(
    sessionmaker: async_sessionmaker[AsyncSession] | None, storage: BaseStorage | None = None
) -> Dispatcher:
    """Создаёт диспетчер: middleware сессии и пользователя, роутеры (fallback — последним).

    Роутеры — объекты модулей, поэтому диспетчер создаётся один раз на процесс.
    """
    dp = Dispatcher(storage=storage, sessionmaker=sessionmaker)
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(DbSessionMiddleware())
        observer.outer_middleware(UserMiddleware())
    dp.include_routers(common.router, agronomist.router, superuser.router, admin.router)
    dp.include_router(fallback.router)
    return dp
