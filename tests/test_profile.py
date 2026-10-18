"""Профиль бота: команды и описание через Bot API (Telegram подменён)."""

from aiogram.methods import SetMyCommands, SetMyDescription, SetMyShortDescription

from bot import texts
from bot.profile import setup_profile
from tests.telegram import make_bot


async def test_setup_profile_calls_api() -> None:
    bot, rec = make_bot()
    await setup_profile(bot)
    commands, short, full = rec.requests
    assert isinstance(commands, SetMyCommands)
    assert [c.command for c in commands.commands] == ["start", "ping"]
    assert isinstance(short, SetMyShortDescription)
    assert len(short.short_description) <= 120  # лимит Telegram
    assert isinstance(full, SetMyDescription)
    assert full.description == texts.BOT_DESCRIPTION
    assert len(full.description) <= 512  # лимит Telegram


async def test_setup_profile_survives_api_error() -> None:
    bot, rec = make_bot()

    async def fail(*args, **kwargs):
        raise RuntimeError("нет сети")

    rec.make_request = fail
    await setup_profile(bot)  # не падает
