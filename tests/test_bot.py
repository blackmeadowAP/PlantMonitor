"""Бот: регистрация, меню по ролям, выдача кодов (Telegram подменён)."""

from collections.abc import AsyncIterator

import pytest
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import SendMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot import keyboards, texts
from bot.app import create_dispatcher
from bot.keyboards import ConsentCb, InviteOrgCb, InviteRegionCb
from core.models import Invite, User, UserRole
from core.services import invites
from tests.factories import World, make_world
from tests.telegram import BOT_USERNAME, callback_update, make_bot, message_update

pytestmark = pytest.mark.db

NEW_TG_ID = 7000


@pytest.fixture
async def world(session: AsyncSession) -> World:
    world = await make_world(session)
    await session.commit()
    return world


@pytest.fixture(scope="session")
def _dispatcher() -> Dispatcher:
    # Роутеры модульные — диспетчер один на все тесты
    return create_dispatcher(sessionmaker=None)


@pytest.fixture
def dp(_dispatcher: Dispatcher, sessionmaker: async_sessionmaker[AsyncSession]) -> Dispatcher:
    """Диспетчер с чистым FSM и сессиями внутри тестовой транзакции."""
    _dispatcher.fsm.storage = MemoryStorage()
    _dispatcher["sessionmaker"] = sessionmaker
    return _dispatcher


@pytest.fixture
async def tg() -> AsyncIterator:
    bot, recorder = make_bot()
    yield bot, recorder
    await bot.session.close()


def menu_buttons(method: SendMessage) -> list[str]:
    return [b.text for row in method.reply_markup.keyboard for b in row]


async def test_ping(dp: Dispatcher, tg) -> None:
    bot, rec = tg
    await dp.feed_update(bot, message_update(NEW_TG_ID, "/ping"))
    assert rec.texts() == [texts.PONG]


async def test_start_without_code(dp: Dispatcher, tg) -> None:
    bot, rec = tg
    await dp.feed_update(bot, message_update(NEW_TG_ID, "/start"))
    assert rec.texts() == [texts.ASK_CODE]


async def test_full_registration(dp: Dispatcher, tg, session: AsyncSession, world: World) -> None:
    bot, rec = tg
    invite = await invites.create_invite(
        session, world.agronomist, UserRole.worker, org_id=world.org.id
    )
    await session.commit()

    await dp.feed_update(bot, message_update(NEW_TG_ID, f"/start {invite.code}"))
    assert rec.texts()[-1] == texts.ASK_NAME
    await dp.feed_update(bot, message_update(NEW_TG_ID, "Иван"))
    assert rec.texts()[-1] == texts.BAD_NAME
    await dp.feed_update(bot, message_update(NEW_TG_ID, "Иванов Иван"))
    assert rec.texts()[-1] == texts.ASK_CONSENT
    await dp.feed_update(bot, callback_update(NEW_TG_ID, ConsentCb(agree=True).pack()))

    welcome = rec.requests[-1]
    assert isinstance(welcome, SendMessage)
    assert welcome.text.startswith("Иванов Иван, добро пожаловать")
    assert menu_buttons(welcome) == [b for row in keyboards.MENU_ROWS[UserRole.worker] for b in row]

    user = await session.scalar(select(User).where(User.tg_id == NEW_TG_ID))
    assert (user.role, user.org_id, user.full_name) == (
        UserRole.worker,
        world.org.id,
        "Иванов Иван",
    )
    await session.refresh(invite)
    assert invite.used_by == user.id

    # Повторно код не срабатывает
    await dp.feed_update(bot, message_update(NEW_TG_ID + 1, f"/start {invite.code}"))
    assert rec.texts()[-1] == texts.CODE_USED


async def test_consent_declined(dp: Dispatcher, tg, session: AsyncSession, world: World) -> None:
    bot, rec = tg
    invite = await invites.create_invite(
        session, world.agronomist, UserRole.worker, org_id=world.org.id
    )
    await session.commit()
    await dp.feed_update(bot, message_update(NEW_TG_ID, f"/start {invite.code}"))
    await dp.feed_update(bot, message_update(NEW_TG_ID, "Иванов Иван"))
    await dp.feed_update(bot, callback_update(NEW_TG_ID, ConsentCb(agree=False).pack()))
    assert rec.texts()[-1] == texts.REGISTRATION_CANCELLED
    assert await session.scalar(select(User).where(User.tg_id == NEW_TG_ID)) is None
    await session.refresh(invite)
    assert invite.used_by is None


async def test_bad_code(dp: Dispatcher, tg) -> None:
    bot, rec = tg
    await dp.feed_update(bot, message_update(NEW_TG_ID, "/start NOSUCH22"))
    assert rec.texts() == [texts.CODE_NOT_FOUND]


@pytest.mark.parametrize("role_attr", ["worker", "agronomist", "superuser", "admin"])
async def test_menu_per_role(dp: Dispatcher, tg, world: World, role_attr: str) -> None:
    """Каждая роль видит своё меню."""
    bot, rec = tg
    user = getattr(world, role_attr)
    await dp.feed_update(bot, message_update(user.tg_id, "/start"))
    expected = [b for row in keyboards.MENU_ROWS[user.role] for b in row]
    assert menu_buttons(rec.last()) == expected


def test_menus_differ() -> None:
    menus = [frozenset(b for row in rows for b in row) for rows in keyboards.MENU_ROWS.values()]
    assert len(set(menus)) == len(menus)


async def test_inactive_user_blocked(dp: Dispatcher, tg, world: World) -> None:
    bot, rec = tg
    await dp.feed_update(bot, message_update(world.inactive_agronomist.tg_id, "/start"))
    assert rec.texts() == [texts.ACCOUNT_DISABLED]


async def test_agronomist_invites_worker(
    dp: Dispatcher, tg, session: AsyncSession, world: World
) -> None:
    bot, rec = tg
    await dp.feed_update(bot, message_update(world.agronomist.tg_id, texts.BTN_INVITE_WORKER))
    invite = await session.scalar(select(Invite).where(Invite.created_by == world.agronomist.id))
    assert (invite.role, invite.org_id) == (UserRole.worker, world.org.id)
    assert f"https://t.me/{BOT_USERNAME}?start={invite.code}" in rec.texts()[-1]


async def test_worker_cannot_use_agronomist_button(
    dp: Dispatcher, tg, session: AsyncSession, world: World
) -> None:
    bot, rec = tg
    await dp.feed_update(bot, message_update(world.worker.tg_id, texts.BTN_INVITE_WORKER))
    assert rec.texts() == [texts.NOT_READY]
    assert await session.scalar(select(Invite).where(Invite.created_by == world.worker.id)) is None


async def test_superuser_invites_agronomist(
    dp: Dispatcher, tg, session: AsyncSession, world: World
) -> None:
    bot, rec = tg
    await dp.feed_update(bot, message_update(world.superuser.tg_id, texts.BTN_INVITE_AGRONOMIST))
    buttons = [b.text for row in rec.last().reply_markup.inline_keyboard for b in row]
    assert buttons == sorted([world.org.name, world.org2.name])  # чужой области нет

    await dp.feed_update(
        bot, callback_update(world.superuser.tg_id, InviteOrgCb(org_id=world.org2.id).pack())
    )
    invite = await session.scalar(select(Invite).where(Invite.created_by == world.superuser.id))
    assert (invite.role, invite.org_id) == (UserRole.agronomist, world.org2.id)


async def test_superuser_forged_callback_for_foreign_org(
    dp: Dispatcher, tg, session: AsyncSession, world: World
) -> None:
    """Подделанная кнопка с чужим предприятием отклоняется сервисом."""
    bot, rec = tg
    await dp.feed_update(
        bot,
        callback_update(world.superuser.tg_id, InviteOrgCb(org_id=world.foreign_org.id).pack()),
    )
    assert rec.last().text == texts.NO_ACCESS
    assert (
        await session.scalar(select(Invite).where(Invite.created_by == world.superuser.id)) is None
    )


async def test_admin_invites_superuser(
    dp: Dispatcher, tg, session: AsyncSession, world: World
) -> None:
    bot, rec = tg
    await dp.feed_update(bot, message_update(world.admin.tg_id, texts.BTN_CREATE_SUPERUSER))
    await dp.feed_update(
        bot,
        callback_update(world.admin.tg_id, InviteRegionCb(region_id=world.other_region.id).pack()),
    )
    invite = await session.scalar(select(Invite).where(Invite.created_by == world.admin.id))
    assert (invite.role, invite.region_id) == (UserRole.superuser, world.other_region.id)
    assert invite.code in rec.texts()[-1]
