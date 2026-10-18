"""Пользователи: поиск и регистрация по коду."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import User
from core.services.invites import get_valid_invite

NAME_MIN_LEN = 3
NAME_MAX_LEN = 100


class AlreadyRegistered(Exception):
    """Telegram-аккаунт уже зарегистрирован."""


async def get_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
    """Пользователь по Telegram ID."""
    return await session.scalar(select(User).where(User.tg_id == tg_id))


def clean_full_name(text: str) -> str | None:
    """Фамилия и имя: минимум два слова, разумная длина. None — если не подходит."""
    name = " ".join(text.split())
    if not NAME_MIN_LEN <= len(name) <= NAME_MAX_LEN or len(name.split()) < 2:
        return None
    if any(ch.isdigit() for ch in name) or name.startswith("/"):
        return None
    return name


async def register(session: AsyncSession, tg_id: int, code: str, full_name: str) -> User:
    """Создаёт пользователя по коду и гасит код. Согласие фиксируется в момент регистрации.

    Код перепроверяется под блокировкой строки: два аккаунта не зарегистрируются по одному коду.
    Коммит — на вызывающей стороне.
    """
    if await get_by_tg_id(session, tg_id) is not None:
        raise AlreadyRegistered
    invite = await get_valid_invite(session, code, for_update=True)
    now = datetime.now(UTC)
    user = User(
        tg_id=tg_id,
        full_name=full_name,
        role=invite.role,
        org_id=invite.org_id,
        region_id=invite.region_id,
        consent_at=now,
    )
    session.add(user)
    await session.flush()
    invite.used_by = user.id
    invite.used_at = now
    await session.flush()
    return user
