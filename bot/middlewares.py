"""Middleware: сессия БД и текущий пользователь для каждого обновления."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot import texts
from core.services import users


class DbSessionMiddleware(BaseMiddleware):
    """Открывает сессию на обновление; коммит — если хэндлер завершился без ошибки.

    Фабрика сессий берётся из данных диспетчера: dp["sessionmaker"].
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        sessionmaker: async_sessionmaker[AsyncSession] = data["sessionmaker"]
        async with sessionmaker() as session:
            data["session"] = session
            result = await handler(event, data)
            await session.commit()
            return result


class UserMiddleware(BaseMiddleware):
    """Кладёт в data["user"] пользователя (или None). Деактивированных дальше не пускает."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        user = await users.get_by_tg_id(data["session"], tg_user.id) if tg_user else None
        if user is not None and not user.is_active:
            if isinstance(event, Message):
                await event.answer(texts.ACCOUNT_DISABLED)
            elif isinstance(event, CallbackQuery):
                await event.answer(texts.ACCOUNT_DISABLED, show_alert=True)
            return None
        data["user"] = user
        return await handler(event, data)
