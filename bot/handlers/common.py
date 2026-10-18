"""Общие команды, доступные всем."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot import texts

router = Router(name="common")


@router.message(Command("ping"))
async def cmd_ping(message: Message) -> None:
    """Проверка, что бот жив."""
    await message.answer(texts.PONG)
