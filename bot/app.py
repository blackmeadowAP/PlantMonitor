"""Сборка диспетчера бота."""

from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage

from bot.handlers import common


def create_dispatcher(storage: BaseStorage | None = None) -> Dispatcher:
    """Создаёт диспетчер и подключает роутеры."""
    dp = Dispatcher(storage=storage)
    dp.include_router(common.router)
    return dp
