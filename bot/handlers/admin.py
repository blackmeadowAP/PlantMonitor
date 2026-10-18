"""Администратор."""

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot import keyboards, texts
from bot.filters import RoleFilter
from bot.invites import invite_text
from bot.keyboards import InviteRegionCb
from core.models import Region, User, UserRole
from core.services import invites, territory
from core.services.access import AccessDenied

router = Router(name="admin")
router.message.filter(RoleFilter(UserRole.admin))
router.callback_query.filter(RoleFilter(UserRole.admin))


@router.message(F.text == texts.BTN_CREATE_SUPERUSER)
async def invite_superuser(message: Message, session: AsyncSession) -> None:
    """Выбор области для кода суперпользователя."""
    regions = await territory.list_regions(session)
    if not regions:
        await message.answer(texts.NO_REGIONS)
        return
    await message.answer(texts.CHOOSE_REGION, reply_markup=keyboards.choose_region(regions))


@router.callback_query(InviteRegionCb.filter())
async def invite_superuser_region(
    callback: CallbackQuery,
    callback_data: InviteRegionCb,
    bot: Bot,
    session: AsyncSession,
    user: User,
) -> None:
    region = await session.get(Region, callback_data.region_id)
    if region is None:
        await callback.answer(texts.NO_ACCESS, show_alert=True)
        return
    try:
        invite = await invites.create_invite(session, user, UserRole.superuser, region_id=region.id)
    except AccessDenied:
        await callback.answer(texts.NO_ACCESS, show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(await invite_text(bot, invite, region.name), parse_mode="HTML")
