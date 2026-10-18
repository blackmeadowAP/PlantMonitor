"""Фильтры хэндлеров."""

from typing import Any

from aiogram.filters import Filter
from aiogram.types import TelegramObject

from core.models import User, UserRole


class RoleFilter(Filter):
    """Пропускает только зарегистрированных пользователей с одной из ролей.

    Это удобство для маршрутизации; права на данные проверяет сервисный слой.
    """

    def __init__(self, *roles: UserRole) -> None:
        self.roles = roles

    async def __call__(self, event: TelegramObject, user: User | None = None, **_: Any) -> bool:
        return user is not None and user.role in self.roles
