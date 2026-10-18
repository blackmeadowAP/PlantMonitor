"""Подмена Telegram Bot API: запросы бота записываются, сеть не используется."""

from datetime import UTC, datetime
from itertools import count
from typing import Any

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import GetMe, TelegramMethod
from aiogram.types import CallbackQuery, Chat, Message, Update
from aiogram.types import User as TgUser

BOT_USERNAME = "agro_test_bot"
_ids = count(1)


class RecordingSession(BaseSession):
    """Сессия aiogram, которая отвечает заглушками и запоминает вызовы."""

    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []

    async def make_request(self, bot: Bot, method: TelegramMethod[Any], timeout=None) -> Any:  # noqa: ASYNC109
        self.requests.append(method)
        if isinstance(method, GetMe):
            return TgUser(id=1, is_bot=True, first_name="Бот", username=BOT_USERNAME)
        if getattr(method, "chat_id", None) is not None:
            return Message(
                message_id=next(_ids),
                date=datetime.now(UTC),
                chat=Chat(id=method.chat_id, type="private"),
                text=getattr(method, "text", None),
            )
        return True

    async def close(self) -> None:
        pass

    async def stream_content(self, *args: Any, **kwargs: Any):  # pragma: no cover
        raise NotImplementedError
        yield b""

    def texts(self) -> list[str]:
        """Тексты всех отправленных и отредактированных сообщений."""
        return [m.text for m in self.requests if getattr(m, "text", None)]

    def last(self) -> TelegramMethod[Any]:
        return self.requests[-1]


def make_bot() -> tuple[Bot, RecordingSession]:
    session = RecordingSession()
    return Bot(token="42:TEST", session=session), session


def _tg_user(tg_id: int) -> TgUser:
    return TgUser(id=tg_id, is_bot=False, first_name="Тест")


def message_update(tg_id: int, text: str) -> Update:
    return Update(
        update_id=next(_ids),
        message=Message(
            message_id=next(_ids),
            date=datetime.now(UTC),
            chat=Chat(id=tg_id, type="private"),
            from_user=_tg_user(tg_id),
            text=text,
        ),
    )


def callback_update(tg_id: int, data: str) -> Update:
    return Update(
        update_id=next(_ids),
        callback_query=CallbackQuery(
            id=str(next(_ids)),
            from_user=_tg_user(tg_id),
            chat_instance="test",
            data=data,
            message=Message(
                message_id=next(_ids),
                date=datetime.now(UTC),
                chat=Chat(id=tg_id, type="private"),
                from_user=TgUser(id=1, is_bot=True, first_name="Бот"),
                text="…",
            ),
        ),
    )
