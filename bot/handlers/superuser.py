"""Суперпользователь."""

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot import keyboards, texts
from bot.filters import RoleFilter
from bot.invites import invite_text
from bot.keyboards import InviteOrgCb
from core.models import Organization, User, UserRole
from core.services import invites, territory
from core.services.access import AccessDenied

router = Router(name="superuser")
router.message.filter(RoleFilter(UserRole.superuser))
router.callback_query.filter(RoleFilter(UserRole.superuser))


@router.message(F.text == texts.BTN_INVITE_AGRONOMIST)
async def invite_agronomist(message: Message, session: AsyncSession, user: User) -> None:
    """Выбор предприятия своей области."""
    orgs = await territory.list_orgs_for(session, user)
    if not orgs:
        await message.answer(texts.NO_ORGS)
        return
    await message.answer(texts.CHOOSE_ORG, reply_markup=keyboards.choose_org(orgs))


@router.callback_query(InviteOrgCb.filter())
async def invite_agronomist_org(
    callback: CallbackQuery,
    callback_data: InviteOrgCb,
    bot: Bot,
    session: AsyncSession,
    user: User,
) -> None:
    try:
        invite = await invites.create_invite(
            session, user, UserRole.agronomist, org_id=callback_data.org_id
        )
    except AccessDenied:
        await callback.answer(texts.NO_ACCESS, show_alert=True)
        return
    org = await session.get(Organization, callback_data.org_id)
    await callback.answer()
    await callback.message.edit_text(await invite_text(bot, invite, org.name), parse_mode="HTML")
