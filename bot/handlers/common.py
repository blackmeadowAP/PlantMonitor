"""Общие команды и регистрация по коду (docs/04, «Регистрация»)."""

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot import keyboards, texts
from bot.keyboards import ConsentCb
from bot.states import Registration
from core.models import User
from core.services import invites, users
from core.services.invites import InviteError, InviteProblem

router = Router(name="common")

INVITE_PROBLEM_TEXTS = {
    InviteProblem.not_found: texts.CODE_NOT_FOUND,
    InviteProblem.used: texts.CODE_USED,
    InviteProblem.expired: texts.CODE_EXPIRED,
}


@router.message(Command("ping"))
async def cmd_ping(message: Message) -> None:
    """Проверка, что бот жив."""
    await message.answer(texts.PONG)


async def show_menu(message: Message, user: User, prefix: str | None = None) -> None:
    """Меню роли с необязательным текстом перед ним."""
    await message.answer(prefix or texts.MENU_HINT, reply_markup=keyboards.main_menu(user.role))


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
) -> None:
    """/start [код]: зарегистрированному — меню, новому — проверка кода и запрос имени."""
    await state.clear()
    if user is not None:
        await show_menu(message, user, texts.ALREADY_REGISTERED if command.args else None)
        return
    if not command.args:
        await message.answer(texts.ASK_CODE)
        return
    try:
        invite = await invites.get_valid_invite(session, command.args)
    except InviteError as e:
        await message.answer(INVITE_PROBLEM_TEXTS[e.problem])
        return
    await state.set_state(Registration.name)
    await state.update_data(code=invite.code)
    await message.answer(texts.ASK_NAME)


@router.message(Registration.name, F.text)
async def registration_name(message: Message, state: FSMContext) -> None:
    name = users.clean_full_name(message.text)
    if name is None:
        await message.answer(texts.BAD_NAME)
        return
    await state.update_data(full_name=name)
    await state.set_state(Registration.consent)
    await message.answer(texts.ASK_CONSENT, reply_markup=keyboards.consent())


@router.message(Registration.name)
async def registration_name_not_text(message: Message) -> None:
    await message.answer(texts.BAD_NAME)


@router.callback_query(Registration.consent, ConsentCb.filter())
async def registration_consent(
    callback: CallbackQuery,
    callback_data: ConsentCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    if not callback_data.agree:
        await callback.message.answer(texts.REGISTRATION_CANCELLED)
        return
    try:
        user = await users.register(session, callback.from_user.id, data["code"], data["full_name"])
    except InviteError as e:
        await callback.message.answer(INVITE_PROBLEM_TEXTS[e.problem])
        return
    except users.AlreadyRegistered:
        await callback.message.answer(texts.ALREADY_REGISTERED)
        return
    welcome = texts.WELCOME.format(name=user.full_name, role=texts.ROLE_TITLES[user.role])
    await show_menu(callback.message, user, welcome)


@router.message(Registration.consent)
async def registration_consent_reminder(message: Message) -> None:
    await message.answer(texts.ASK_CONSENT, reply_markup=keyboards.consent())


@router.callback_query(StateFilter(None), ConsentCb.filter())
async def stale_consent(callback: CallbackQuery) -> None:
    """Кнопка согласия из старого сообщения."""
    await callback.answer(texts.REGISTRATION_CANCELLED, show_alert=True)
