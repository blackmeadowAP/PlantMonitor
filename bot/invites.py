"""Оформление выданного кода-приглашения."""

import html
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.utils.deep_linking import create_start_link

from bot import texts
from core.config import get_settings
from core.models import Invite


async def invite_text(bot: Bot, invite: Invite, scope: str) -> str:
    """Сообщение с кодом, ссылкой и сроком действия (время — Europe/Minsk)."""
    expires = invite.expires_at.astimezone(ZoneInfo(get_settings().tz_name))
    return texts.INVITE_CREATED.format(
        role=texts.ROLE_TITLES[invite.role],
        scope=html.escape(scope),
        code=invite.code,
        expires=expires.strftime("%d.%m.%Y %H:%M"),
        link=await create_start_link(bot, invite.code),
    )
