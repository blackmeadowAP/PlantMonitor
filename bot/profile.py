"""Профиль бота в Telegram: команды и описание, устанавливаются при запуске."""

import logging

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

from bot import texts

logger = logging.getLogger(__name__)

COMMANDS = [
    BotCommand(command="start", description=texts.CMD_START),
    BotCommand(command="ping", description=texts.CMD_PING),
]


async def setup_profile(bot: Bot) -> None:
    """Обновляет команды и описание. Ошибка API не мешает запуску бота."""
    try:
        await bot.set_my_commands(COMMANDS, scope=BotCommandScopeDefault())
        await bot.set_my_short_description(texts.BOT_SHORT_DESCRIPTION)
        await bot.set_my_description(texts.BOT_DESCRIPTION)
    except Exception:
        logger.warning("Не удалось обновить профиль бота", exc_info=True)
        return
    logger.info("Профиль бота обновлён: %d команд", len(COMMANDS))
