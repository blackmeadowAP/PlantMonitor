"""Обработка всего, что не поймали другие роутеры. Подключается последним."""

from aiogram import F, Router
from aiogram.types import Message

from bot import keyboards, texts
from core.models import User

router = Router(name="fallback")


@router.message(F.text.in_(keyboards.ALL_MENU_BUTTONS))
async def menu_not_ready(message: Message, user: User | None) -> None:
    """Разделы меню, которые появятся на следующих шагах."""
    if user is None:
        await message.answer(texts.ASK_CODE)
        return
    await message.answer(texts.NOT_READY, reply_markup=keyboards.main_menu(user.role))


@router.message()
async def unknown(message: Message, user: User | None) -> None:
    if user is None:
        await message.answer(texts.ASK_CODE)
        return
    await message.answer(texts.MENU_HINT, reply_markup=keyboards.main_menu(user.role))
