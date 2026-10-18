"""Точка входа бота: python -m bot (long polling)."""

import asyncio
import logging

from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage

from bot.app import create_dispatcher
from core.config import get_settings
from core.logging import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Запуск long polling с FSM-хранилищем в Redis."""
    settings = get_settings()
    setup_logging(settings.log_level)
    token = settings.bot_token.get_secret_value()
    if not token:
        raise SystemExit("BOT_TOKEN не задан: заполните .env")

    bot = Bot(token=token)
    storage = RedisStorage.from_url(settings.redis_url)
    dp = create_dispatcher(storage)
    logger.info("Бот запускается (long polling)")
    try:
        await dp.start_polling(bot)
    finally:
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
