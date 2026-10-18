"""Сборка диспетчера бота."""

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.base import BaseStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.handlers import admin, agronomist, common, fallback, superuser
from bot.middlewares import DbSessionMiddleware, UserMiddleware
from core.config import Settings


def create_bot(settings: Settings) -> Bot:
    """Бот с адресом Bot API из настроек (TELEGRAM_API_URL)."""
    token = settings.bot_token.get_secret_value()
    if not token:
        raise SystemExit("BOT_TOKEN не задан: заполните .env")
    server = TelegramAPIServer.from_base(settings.telegram_api_url.rstrip("/"))
    return Bot(token=token, session=AiohttpSession(api=server))


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
