"""Бот: команда /ping (без реальной сети Telegram)."""

from unittest.mock import AsyncMock

from bot import texts
from bot.app import create_dispatcher
from bot.handlers import common


async def test_ping_answers_pong() -> None:
    message = AsyncMock()
    await common.cmd_ping(message)
    message.answer.assert_awaited_once_with(texts.PONG)


def test_dispatcher_includes_common_router() -> None:
    dp = create_dispatcher()
    assert common.router in dp.sub_routers
