"""Агроном."""

from aiogram import Bot, F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot import texts
from bot.filters import RoleFilter
from bot.invites import invite_text
from core.models import Organization, User, UserRole
from core.services import invites

router = Router(name="agronomist")
router.message.filter(RoleFilter(UserRole.agronomist))


@router.message(F.text == texts.BTN_INVITE_WORKER)
async def invite_worker(message: Message, bot: Bot, session: AsyncSession, user: User) -> None:
    """Код работника для своего предприятия."""
    invite = await invites.create_invite(session, user, UserRole.worker, org_id=user.org_id)
    org = await session.get(Organization, user.org_id)
    await message.answer(await invite_text(bot, invite, org.name), parse_mode="HTML")
